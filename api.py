from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Podcast RAG API")

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

# Lazy load so Uvicorn can start instantly without heavy imports blocking the GIL
_generate_answer_func = None

def get_generate_answer():
    global _generate_answer_func
    if _generate_answer_func is None:
        # This string of imports takes ~60s on first request
        from src.query import generate_answer
        _generate_answer_func = generate_answer
    return _generate_answer_func

@app.get("/")
def read_root():
    return {"status": "online", "message": "Podcast RAG API is running (Lazy Loaded)"}

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        def blocking_worker(question):
            func = get_generate_answer()
            return func(question)
            
        result = await loop.run_in_executor(None, blocking_worker, request.question)
        return QueryResponse(
            answer=result["answer"],
            graph_data=result["graph_data"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("🚀 [SERVER BOOT] Python execution started...", flush=True)
    port_str = os.environ.get("PORT", "8000")
    if not port_str: port_str = "8000"
    port = int(port_str)
    print(f"🚀 [SERVER BOOT] Attempting to bind to 0.0.0.0:{port}...", flush=True)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
