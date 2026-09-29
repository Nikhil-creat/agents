"""Multi-model router: cheap/fast for planning, strong reasoning for critique. Offline stub if no keys."""
import os, json

ROLES = {"planner": "openai", "executor": "openai", "critic": "anthropic", "writer": "anthropic"}

def _model(provider):
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    if provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-sonnet-4-5", temperature=0.2)
    return None

def ask(role: str, prompt: str) -> str:
    order = [ROLES[role], "anthropic" if ROLES[role] == "openai" else "openai"]  # failover
    for p in order:
        m = _model(p)
        if m:
            try: return m.invoke(prompt).content
            except Exception: continue
    return _offline(role, prompt)

def _offline(role, prompt):
    if role == "planner": return json.dumps(["search: " + prompt[-80:], "calc: 2*21", "summarize findings"])
    if role == "critic": return json.dumps({"score": 0.9, "feedback": "ok"})
    return "Offline mode: add an API key for real model output."
