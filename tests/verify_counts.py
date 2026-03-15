import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import get_connection
from src.embeddings import get_chroma_client

def verify_counts():
    print("Verifying Backfill Counts...")
    
    # 1. Check SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as cnt FROM chunks")
    sqlite_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT count(*) as cnt FROM chunks WHERE type='child'")
    sqlite_child_count = cursor.fetchone()['cnt']
    conn.close()
    
    print(f"SQLite Total Chunks: {sqlite_count}")
    print(f"SQLite Child Chunks: {sqlite_child_count}")
    
    # 2. Check Chroma
    client = get_chroma_client()
    collection = client.get_collection("podcasts")
    chroma_count = collection.count()
    
    print(f"Chroma Total Vectors: {chroma_count}")
    
    # Validation logic
    # Chroma count should be >= SQLite child count (accounting for previous tests)
    if chroma_count >= sqlite_child_count:
        print("SUCCESS: Chroma count matches or exceeds SQLite child count.")
    else:
        print(f"FAIL: Chroma count {chroma_count} is LESS than SQLite child count {sqlite_child_count}.")
        return False
        
    return True

if __name__ == "__main__":
    verify_counts()
