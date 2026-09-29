import os, json, asyncio, redis
from celery import Celery
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from .graph import build
from .tools import load_mcp

URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery = Celery("nexus", broker=URL, backend=URL)
r = redis.from_url(URL)

def pub(run_id, ev):
    msg = json.dumps(ev, default=str)
    r.rpush(f"run:{run_id}:log", msg); r.publish(f"run:{run_id}", msg)

@celery.task(name="run_graph")
def run_graph(run_id, task=None, resume=None):
    asyncio.run(load_mcp())
    with PostgresSaver.from_conn_string(os.environ["PG_URL"]) as cp:
        cp.setup()
        g = build(cp)
        cfg = {"configurable": {"thread_id": run_id}}
        inp = Command(resume=resume) if resume is not None else {"task": task, "results": []}
        try:
            for ev in g.stream(inp, cfg, stream_mode="updates"): pub(run_id, ev)
            pub(run_id, {"__done__": True})
        except Exception as e:
            pub(run_id, {"__error__": str(e)})

from celery.signals import worker_ready
@worker_ready.connect
def _metrics(**_):
    from prometheus_client import start_http_server
    start_http_server(9100)  # scrape http://localhost:9100/metrics
