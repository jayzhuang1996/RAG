import uuid

def chunk_text(text, chunk_size, overlap):
    """
    Simple character-based chunker.
    Args:
        text (str): Input text.
        chunk_size (int): Size in characters.
        overlap (int): Overlap in characters.
    Returns:
        list of dicts: [{'text': str, 'start_char': int, 'end_char': int}]
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_text = text[start:end]
        
        # specific fix: ensure we don't cut words in half ideally, but for MVP simple slicing is fine.
        # Improvement: Look for nearest space?
        # Let's do a quick "nearest space" adjustment if we are not at end
        if end < text_len:
            # Look for last space within the chunk to split nicely
            last_space = chunk_text.rfind(' ')
            if last_space != -1 and last_space > chunk_size * 0.5: # Only if space is in second half
                end = start + last_space + 1 # Include the space
                chunk_text = text[start:end]
        
        chunks.append({
            'text': chunk_text,
            'start_char': start,
            'end_char': end
        })
        
        start += (chunk_size - overlap)
        
    return chunks

def create_parent_child_chunks(video_id, full_text):
    """
    Generates Parent and Child chunks for a video.
    
    Strategy:
    1. Create Parent Chunks (Large context).
    2. Create Child Chunks (Small, for vector search) from EACH Parent? 
       - Actually, typical Parent-Child RAG: Fetch Parents, search Children.
       - But Children need to be subsets of Parents.
       - Alternative: Chunk text into Children. Map each Child to a simpler "Window" around it?
       - Or: Chunk text into Parents. Then chunk Parent into Children.
    
    Let's go with: Chunk text into Parents. Then chunk each Parent text into Children.
    This ensures every Child has exactly one Parent.
    
    Sizes:
    - Parent: ~3000 chars (~750 tokens)
    - Child: ~1000 chars (~250 tokens) -> Fits MiniLM (256 tokens)
    - Overlap: 200 chars
    """
    
    # 1. Generate Parent Chunks
    parent_chunks_data = chunk_text(full_text, chunk_size=3000, overlap=200)
    
    all_chunks = []
    
    for p_idx, p_data in enumerate(parent_chunks_data):
        parent_id = str(uuid.uuid4())
        
        # Add Parent Chunk
        all_chunks.append({
            'id': parent_id,
            'video_id': video_id,
            'text': p_data['text'],
            'type': 'parent',
            'parent_id': None,
            'chunk_index': p_idx,
            'start_char': p_data['start_char'], # We store char indices for now, mapping to time later if needed
            'end_char': p_data['end_char']
        })
        
        # 2. Generate Child Chunks for this Parent
        # We chunk the PARENT'S text.
        child_chunks_data = chunk_text(p_data['text'], chunk_size=1000, overlap=100)
        
        for c_idx, c_data in enumerate(child_chunks_data):
            child_id = str(uuid.uuid4())
            all_chunks.append({
                'id': child_id,
                'video_id': video_id,
                'text': c_data['text'],
                'type': 'child',
                'parent_id': parent_id,
                'chunk_index': c_idx, # relative to parent
                'start_char': p_data['start_char'] + c_data['start_char'], # Absolute position
                'end_char': p_data['start_char'] + c_data['end_char']
            })
            
    return all_chunks
