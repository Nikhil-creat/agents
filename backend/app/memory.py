"""Short-term memory = LangGraph checkpoints in Postgres. Long-term = semantic vectors in ChromaDB."""
import os, uuid
_col = None
def col():
    global _col
    if _col is None:
        import chromadb
        c = chromadb.HttpClient(host=os.getenv("CHROMA_HOST", "chroma"), port=8000)
        _col = c.get_or_create_collection("nexus_memory")
    return _col

def recall(q, k=3):
    try: return (col().query(query_texts=[q], n_results=k)["documents"] or [[]])[0]
    except Exception: return []

def remember(text, meta=None):
    try: col().add(ids=[str(uuid.uuid4())], documents=[text], metadatas=[meta or {"src": "run"}])
    except Exception: pass
