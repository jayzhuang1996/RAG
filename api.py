from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.query import generate_answer

app = FastAPI(title="Podcast RAG API")

from typing import List, Dict, Any

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    graph_data: List[str]
    sources: List[Dict[str, Any]]

@app.get("/")
def read_root():
    return {"status": "online", "message": "Podcast RAG API is running"}

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    try:
        # Note: generate_answer handles retrieval and LLM synthesis
        result = generate_answer(request.question)
        return QueryResponse(
            answer=result["answer"],
            graph_data=result["graph_data"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Railway will inject the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
