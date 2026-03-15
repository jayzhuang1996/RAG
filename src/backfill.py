import os
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import get_connection
from src.chunking import create_parent_child_chunks
from src.embeddings import embed_and_store

from src.db import get_connection, get_supabase_client

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def backfill_chunks(limit=None):
    """Chunk and embed videos needing processing."""
    if USE_SUPABASE:
        supabase = get_supabase_client()
        res_t = supabase.table("viking_transcripts").select("video_id, full_text").execute()
        res_c = supabase.table("viking_chunks").select("video_id").execute()
        processed_ids = {r['video_id'] for r in res_c.data}
        videos_to_process = [r for r in res_t.data if r['video_id'] not in processed_ids]
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.video_id, t.full_text 
            FROM transcripts t
            WHERE t.video_id NOT IN (SELECT DISTINCT video_id FROM chunks)
        """)
        videos_to_process = cursor.fetchall()
    
    print(f"Found {len(videos_to_process)} videos needing chunking/embedding.")
    
    count = 0
    for row in videos_to_process:
        if limit and count >= limit: break
        video_id = row['video_id']
        full_text = row['full_text']
        print(f"Processing video: {video_id}")
        
        try:
            chunks = create_parent_child_chunks(video_id, full_text)
            print(f"  -> Generated {len(chunks)} chunks.")
            
            if USE_SUPABASE:
                # Store all chunks in Supabase (Metadata only, vectors added in next step)
                # But for Supabase, viking_chunks has vector column, so we might want to batch.
                # Actually, embed_and_store handles the vector part for children.
                # We need to upsert parents here first.
                parents = [c for c in chunks if c['type'] == 'parent']
                supabase.table("viking_chunks").upsert([{
                    "id": p['id'], "video_id": p['video_id'], "text": p['text'],
                    "type": p['type'], "parent_id": None, "chunk_index": p['chunk_index']
                } for p in parents]).execute()
                
                # Children are handled by embed_and_store(chunks) if USE_SUPABASE is True
                embed_and_store(chunks)
            else:
                for c in chunks:
                    cursor.execute("""
                        INSERT INTO chunks (id, video_id, text, type, parent_id, chunk_index)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (c['id'], c['video_id'], c['text'], c['type'], c['parent_id'], c['chunk_index']))
                embed_and_store(chunks)
                conn.commit()
            
            print(f"  -> Successfully backfilled {video_id}")
            
        except Exception as e:
            print(f"  -> Failed to backfill {video_id}: {e}")
            if not USE_SUPABASE: conn.rollback()
            
        count += 1
        
    if not USE_SUPABASE: conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    backfill_chunks(limit=args.limit)
