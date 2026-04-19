import os
import sys
import chromadb
from chromadb.config import Settings
import cohere

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client

# Constants
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chroma_db')
COLLECTION_NAME = "podcasts"
EMBEDDING_MODEL_NAME = "embed-english-light-v3.0"  # Cohere model with 384 dimensions (matches existing DB schema!)
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

# Global instances
_chroma_client = None
_cohere_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(allow_reset=True))
    return _chroma_client

def get_cohere_client():
    global _cohere_client
    if _cohere_client is None:
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable is required")
        _cohere_client = cohere.Client(api_key)
    return _cohere_client

def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

def get_embeddings(texts):
    """Fetch embeddings from Cohere API."""
    client = get_cohere_client()
    # input_type="search_document" is recommended by Cohere when storing to a database
    response = client.embed(
        texts=texts,
        model=EMBEDDING_MODEL_NAME,
        input_type="search_document"
    )
    return response.embeddings

def embed_and_store(chunks, batch_size=50):
    """
    Embeds Child chunks and stores them in chosen storage (ChromaDB or Supabase).
    Using Cohere API instead of local PyTorch to avoid Memory crashes.
    """
    child_chunks = [c for c in chunks if c['type'] == 'child']
    if not child_chunks:
        raise ValueError("No child chunks to embed.")

    total = len(child_chunks)
    print(f"Embedding {total} child chunks using Cohere API for {'Supabase' if USE_SUPABASE else 'ChromaDB'}...")

    if USE_SUPABASE:
        supabase = get_supabase_client()
        
    for i in range(0, total, batch_size):
        batch = child_chunks[i : i + batch_size]
        documents = [c['text'] for c in batch]
        
        # Batch call to Cohere API replacing heavy local embedding
        embeddings = get_embeddings(documents)

        if USE_SUPABASE:
            supabase_rows = []
            for j, c in enumerate(batch):
                supabase_rows.append({
                    "id": c['id'],
                    "video_id": c['video_id'],
                    "text": c['text'],
                    "type": c['type'],
                    "parent_id": c['parent_id'],
                    "chunk_index": c['chunk_index'],
                    "embedding": embeddings[j]
                })
            supabase.table("viking_chunks").upsert(supabase_rows).execute()
        else:
            collection = get_collection()
            ids = [c['id'] for c in batch]
            metadatas = [{
                'video_id': c['video_id'],
                'parent_id': c['parent_id'],
                'chunk_index': c['chunk_index'],
                'type': c['type']
            } for c in batch]
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        print(f"  -> Processed batch {i} - {min(i+batch_size, total)}")

def reset_vector_db():
    """Wipes the vector database (Use with caution)"""
    client = get_chroma_client()
    client.reset()
    print("Vector database reset.")
