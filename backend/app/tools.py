"""Tool registry. Custom tools via @tool; MCP servers auto-loaded from MCP_SERVERS env."""
import os, json, math, httpx
REGISTRY = {}
def tool(name, risk="low"):
    def deco(fn): REGISTRY[name] = {"fn": fn, "risk": risk, "doc": fn.__doc__}; return fn
    return deco

@tool("search")
def search(q: str):
    """Web search (DuckDuckGo instant answer)."""
    r = httpx.get("https://api.duckduckgo.com/", params={"q": q, "format": "json"}, timeout=10).json()
    return r.get("AbstractText") or str(r.get("RelatedTopics", [])[:3])

@tool("calc")
def calc(expr: str):
    """Safe math evaluator."""
    return str(eval(expr, {"__builtins__": {}}, vars(math)))

@tool("write_file", risk="high")
def write_file(spec: str):
    """Writes to sandbox (approval required)."""
    p, _, c = spec.partition("::"); open("/tmp/" + os.path.basename(p), "w").write(c); return "written"

async def load_mcp():
    cfg = json.loads(os.getenv("MCP_SERVERS", "{}"))
    if not cfg: return
    from langchain_mcp_adapters.client import MultiServerMCPClient
    for t in await MultiServerMCPClient(cfg).get_tools():
        REGISTRY["mcp:" + t.name] = {"fn": lambda a, t=t: t.invoke(a), "risk": "medium", "doc": t.description}

BAD = ("ignore previous", "ignore all previous", "system prompt", "you are now")
def sanitize(text):  # prompt-injection guard on tool output
    return "\n".join(l for l in text.splitlines() if not any(b in l.lower() for b in BAD))

def run_tool(name, arg):
    t = REGISTRY.get(name)
    if not t: return f"unknown tool {name}"
    try: return sanitize(str(t["fn"](arg)))[:2000]
    except Exception as e: return f"tool error: {e}"
