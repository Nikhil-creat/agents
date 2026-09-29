import uuid, asyncio, os
import redis.asyncio as aredis
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .worker import run_graph, URL

app = FastAPI(title="AGENTS")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
@app.get("/health")
def health(): return {"ok": True}
class Run(BaseModel): task: str
class Resume(BaseModel): approve: bool

@app.post("/runs")
def create(b: Run):
    rid = uuid.uuid4().hex[:12]; run_graph.delay(rid, task=b.task); return {"id": rid}

@app.post("/runs/{rid}/resume")
def resume(rid: str, b: Resume):
    run_graph.delay(rid, resume={"approve": b.approve}); return {"ok": True}

@app.get("/runs/{rid}/stream")
async def stream(rid: str):
    r = aredis.from_url(URL); ps = r.pubsub(); await ps.subscribe(f"run:{rid}")
    async def gen():
        for m in await r.lrange(f"run:{rid}:log", 0, -1): yield f"data: {m.decode()}\n\n"
        while True:
            m = await ps.get_message(ignore_subscribe_messages=True, timeout=15)
            yield f"data: {m['data'].decode()}\n\n" if m else ": ping\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

if os.path.isdir("/frontend"): app.mount("/", StaticFiles(directory="/frontend", html=True))
