import json, operator, time
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from .llm import ask
from .tools import REGISTRY, run_tool
from .memory import recall, remember
from .metrics import TOOL_CALLS, TOOL_LAT

class S(TypedDict):
    task: str; plan: list; context: list; loops: int
    results: Annotated[list, operator.add]
    answer: str; score: float

def n_recall(s): return {"context": recall(s["task"]), "loops": 0}

def n_plan(s):
    tools = {k: v["doc"] for k, v in REGISTRY.items()}
    raw = ask("planner", f"Task: {s['task']}\nMemory: {s['context']}\nTools: {tools}\n"
              'Return ONLY a JSON list of steps formatted "tool: argument".')
    try: plan = json.loads(raw[raw.index("["): raw.rindex("]") + 1])
    except Exception: plan = [f"search: {s['task']}"]
    return {"plan": plan}

def n_guard(s) -> Command:
    risky = [p for p in s["plan"] if REGISTRY.get(p.split(":")[0].strip(), {}).get("risk") == "high"]
    if risky:
        d = interrupt({"type": "approval", "reason": "High-risk tool calls", "steps": risky})
        if not d.get("approve"):
            return Command(goto="synthesize", update={"results": ["Human rejected risky steps."]})
    return Command(goto="execute")

AGENT_OF = {"search": "researcher", "calc": "analyst", "write_file": "operator"}
def _one(step):
    name, _, arg = step.partition(":"); name = name.strip(); t = time.time()
    out = run_tool(name, arg.strip())
    TOOL_CALLS.labels(name).inc(); TOOL_LAT.labels(name).observe(time.time() - t)
    return f"[{AGENT_OF.get(name, 'operator')}/{name}] {out}"

def n_exec(s):  # specialist agents run in parallel
    with ThreadPoolExecutor(4) as ex: return {"results": list(ex.map(_one, s["plan"]))}

def n_critic(s):
    raw = ask("critic", f"Task: {s['task']}\nResults: {s['results']}\nJSON {{score:0-1,feedback}} only.")
    try: sc = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])["score"]
    except Exception: sc = 0.8
    return {"score": sc, "loops": s["loops"] + 1}

def route_critic(s): return "synthesize" if s["score"] >= .7 or s["loops"] >= 2 else "plan"

def n_synth(s):
    return {"answer": ask("writer", f"Answer the task using the evidence.\nTask: {s['task']}\nEvidence: {s['results']}")}

def n_mem(s): remember(f"Q: {s['task']}\nA: {s['answer']}"); return {}

def build(checkpointer):
    g = StateGraph(S)
    for n, f in [("recall", n_recall), ("plan", n_plan), ("guard", n_guard), ("execute", n_exec),
                 ("critic", n_critic), ("synthesize", n_synth), ("remember", n_mem)]: g.add_node(n, f)
    g.add_edge(START, "recall"); g.add_edge("recall", "plan"); g.add_edge("plan", "guard")
    g.add_edge("execute", "critic")
    g.add_conditional_edges("critic", route_critic, ["synthesize", "plan"])
    g.add_edge("synthesize", "remember"); g.add_edge("remember", END)
    return g.compile(checkpointer=checkpointer)
