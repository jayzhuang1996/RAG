import os
import sqlite3
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # We need the SERVICE ROLE key for migration

def migrate():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing Supabase credentials in .env")
        return

    supabase: Client = create_client(url, key)
    
    # 1. Connect to local DB
    conn = sqlite3.connect('data/podcasts.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 2. Migrate Videos
    print("Migrating videos...")
    cursor.execute("SELECT * FROM videos")
    videos = cursor.fetchall()
    for v in videos:
        data = dict(v)
        supabase.table("viking_videos").upsert(data).execute()

    # 3. Migrate Transcripts
    print("Migrating transcripts...")
    cursor.execute("SELECT * FROM transcripts")
    transcripts = cursor.fetchall()
    for t in transcripts:
        data = {
            "video_id": t["video_id"],
            "full_text": t["full_text"],
            "raw_json": t["raw_json"]
        }
        supabase.table("viking_transcripts").upsert(data).execute()

    # 4. Migrate Chunks & Embeddings
    print("Migrating chunks and embeddings...")
    from src.embeddings import get_collection
    collection = get_collection()
    
    cursor.execute("SELECT * FROM chunks")
    chunks = cursor.fetchall()
    for c in chunks:
        # Fetch embedding if child
        embedding = None
        if c["type"] == "child":
            res = collection.get(ids=[c["id"]], include=['embeddings'])
            if res.get('embeddings') is not None and len(res['embeddings']) > 0:
                # Convert ndarray to list for JSON serialization
                embedding = res['embeddings'][0]
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                elif not isinstance(embedding, list):
                    embedding = list(embedding)
        
        data = {
            "id": c["id"],
            "video_id": c["video_id"],
            "text": c["text"],
            "type": c["type"],
            "parent_id": c["parent_id"],
            "start_time": None, # Mapping chars to time not implemented yet
            "end_time": None,
            "chunk_index": c["chunk_index"],
            "embedding": embedding
        }
        supabase.table("viking_chunks").upsert(data).execute()

    # 5. Migrate Metadata (Entities)
    print("Migrating metadata...")
    cursor.execute("SELECT * FROM metadata")
    metadata = cursor.fetchall()
    for m in metadata:
        data = {
            "video_id": m["video_id"],
            "type": m["type"],
            "value": m["value"]
        }
        supabase.table("viking_metadata").insert(data).execute()

    # 6. Migrate Relationships
    print("Migrating relationships...")
    cursor.execute("SELECT * FROM relationships")
    rels = cursor.fetchall()
    for r in rels:
        data = {
            "video_id": r["video_id"],
            "subject": r["subject"],
            "verb": r["verb"],
            "object": r["object"]
        }
        supabase.table("viking_relationships").insert(data).execute()

    print("Migration complete.")
    conn.close()

if __name__ == "__main__":
    migrate()
