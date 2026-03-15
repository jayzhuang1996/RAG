import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chunking import create_parent_child_chunks

def test_chunking():
    print("Testing Parent-Child Chunking...")
    
    # Create dummy text of ~5000 chars
    # "Word " is 5 chars. 1000 words = 5000 chars.
    dummy_text = "Word " * 1000 
    
    chunks = create_parent_child_chunks("test_video_123", dummy_text)
    
    print(f"Total chunks generated: {len(chunks)}")
    
    parents = [c for c in chunks if c['type'] == 'parent']
    children = [c for c in chunks if c['type'] == 'child']
    
    print(f"Parent chunks: {len(parents)}")
    print(f"Child chunks: {len(children)}")
    
    # Validations
    if len(parents) == 0:
        print("FAIL: No parents created.")
        return False
        
    if len(children) == 0:
        print("FAIL: No children created.")
        return False
        
    # Check linkage
    first_parent = parents[0]
    first_parent_children = [c for c in children if c['parent_id'] == first_parent['id']]
    
    print(f"Children for first parent ({first_parent['id']}): {len(first_parent_children)}")
    
    if len(first_parent_children) == 0:
        print("FAIL: First parent has no children linked.")
        return False
        
    # Check sizes
    avg_child_len = sum(len(c['text']) for c in children) / len(children)
    print(f"Average child length: {avg_child_len:.1f} chars (Target ~1000)")
    
    # Check constraint
    max_child_len = max(len(c['text']) for c in children)
    if max_child_len > 1200: # Allow some buffer for word boundary logic
        print(f"WARNING: Max child length {max_child_len} exceeds target 1000 significanly.")
        
    print("SUCCESS: Chunking logic verified.")
    return True

if __name__ == "__main__":
    test_chunking()
