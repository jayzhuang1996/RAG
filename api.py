from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import os
import sys
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── Deferred initialization ──────────────────────────────────────────────────
# We do NOT import src.query at module level because it triggers
# sentence-transformers + ChromaDB loading (~60s on cold start).
# Railway kills the container if it doesn't respond within 15s.
# Instead we start the server immediately and warm up in a background thread.

_ready = False
_init_error = None
_generate_answer = None

def _initialize():
    global _ready, _init_error, _generate_answer
    try:
        logger.info("Starting background initialization...")
        from src.query import generate_answer
        _generate_answer = generate_answer
        # Force-build the BM25 index now so first query is fast
        from src.query import get_retriever
        get_retriever()
        _ready = True
        logger.info("✅ Initialization complete — API is ready")
    except Exception as e:
        _init_error = str(e)
        logger.error(f"❌ Initialization failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start heavy initialization in background thread immediately on startup
    t = threading.Thread(target=_initialize, daemon=True)
    t.start()
    yield

app = FastAPI(title="Podcast RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import List, Dict, Any

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    graph_data: List[Dict[str, str]]
    sources: List[Dict[str, Any]]

@app.get("/")
def read_root():
    """Health check — always responds immediately."""
    return {
        "status": "online",
        "ready": _ready,
        "message": "Podcast RAG API is running" if _ready else "Warming up...",
    }

@app.get("/health")
def health():
    """Railway health check endpoint."""
    if _init_error:
        return JSONResponse(status_code=503, content={"status": "error", "detail": _init_error})
    return {"status": "ok", "ready": _ready}

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    if not _ready:
        if _init_error:
            raise HTTPException(status_code=503, detail=f"Initialization failed: {_init_error}")
        raise HTTPException(status_code=503, detail="API is warming up. Please retry in 30 seconds.")
    try:
        result = _generate_answer(request.question)
        return QueryResponse(
            answer=result["answer"],
            graph_data=result["graph_data"],
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
