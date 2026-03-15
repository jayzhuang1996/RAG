import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.embeddings import embed_and_store, get_chroma_client

def test_embeddings():
    print("Testing Embedding Engine...")
    
    # 1. Create Dummy Chunks
    dummy_chunks = [
        # Parent (should be ignored by embedder)
        {
            'id': 'parent_1',
            'video_id': 'vid_1',
            'text': "This is parent content.",
            'type': 'parent',
            'parent_id': None,
            'chunk_index': 0
        },
        # Child 1
        {
            'id': 'child_1',
            'video_id': 'vid_1',
            'text': "This is child content one.",
            'type': 'child',
            'parent_id': 'parent_1',
            'chunk_index': 0
        },
        # Child 2
        {
            'id': 'child_2',
            'video_id': 'vid_1',
            'text': "This is child content two.",
            'type': 'child',
            'parent_id': 'parent_1',
            'chunk_index': 1
        }
    ]
    
    # 2. Embed and Store
    print("Running embed_and_store...")
    try:
        embed_and_store(dummy_chunks)
    except Exception as e:
        print(f"FAIL: Exception during embedding: {e}")
        return False
        
    # 3. Verify
    print("Verifying storage...")
    client = get_chroma_client()
    collection = client.get_collection("podcasts")
    
    # Get by ID
    results = collection.get(ids=['child_1', 'child_2', 'parent_1'])
    
    found_ids = results['ids']
    print(f"Found IDs in Chroma: {found_ids}")
    
    if 'child_1' in found_ids and 'child_2' in found_ids:
        print("SUCCESS: Found both children.")
    else:
        print("FAIL: Missing children.")
        return False
        
    if 'parent_1' in found_ids:
        print("FAIL: Found parent chunk in Vector DB (should only store children).")
        return False
    else:
        print("SUCCESS: Parent chunk correctly excluded.")
        
    return True

if __name__ == "__main__":
    test_embeddings()
