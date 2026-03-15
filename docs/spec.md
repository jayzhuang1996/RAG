# Podcast RAG - Technical Specification

## 1. Data Ingestion Layer

### scraper.py
- **Library:** `scrapetube`
- **Function:** `fetch_video_ids(channel_url) -> List[str]`
- **Logic:**
    - Iterate through `config/channels.yaml`.
    - Retrieve all video IDs for each channel.
    - Check `podcasts.db` (videos table) for existing IDs.
    - Filter out already processed videos.

### transcripts.py
- **Library:** `youtube-transcript-api`
- **Function:** `fetch_transcript(video_id) -> Dict`
- **Logic:**
    - Attempt to fetch transcript (prefer manual 'en', fallback to auto-generated 'en').
    - If failed (cookies/disabled), update `status='error'` in DB and log.
    - **Rate Limit:** Sleep 2.0 seconds between requests.
    - **Storage:** Save full text to `transcripts.full_text` and raw JSON to `transcripts.raw_json`.

### metadata.py (Layer 6)
- **Model:** Claude 3 Haiku
- **Prompt:** "Extract list of Guests, Companies, and Key Topics from this transcript. Return JSON."
- **Storage:** Insert into `metadata` table.

## 2. Embedding & Storage Layer

### chunking.py
- **Strategy:** Parent-Child
- **Parent Chunk:**
    - Size: 2400 tokens (approx 10-12 mins audio).
    - Purpose: Provided to LLM for context.
- **Child Chunk:**
    - Size: 800 tokens.
    - Overlap: 100 tokens.
    - Relation: Each Child has a `parent_id` linking to the larger context.

### embeddings.py
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Vector DB:** ChromaDB (Local Persisted)
- **Collection Name:** `podcast_chunks`
- **Metadata:**
    - `video_id`, `start_time`, `parent_id`
    - `guest_names` (for pre-filtering)

## 3. Retrieval Layer (The "Secret Sauce")

### retrieval.py
- **Class:** `HybridRetriever`
- **Components:**
    1.  **BM25:** Built in-memory from `transcripts.full_text` at startup. Keys = `parent_id`.
    2.  **Chroma:** Semantic search returns `child_chunks`. Move up to `parent_id`.
- **Flow:**
    1.  `search_bm25(query, k=20)` -> List[ParentIDs]
    2.  `search_chroma(query, k=20)` -> List[ParentIDs] (via Child)
    3.  `rrf_fusion(list1, list2)` -> Top 10 ParentIDs.
    4.  `cohere.rerank(query, documents=top_10)` -> Top 5 ParentIDs.

## 4. Query Interface

### query.py
- **Model:** Claude 3.5 Sonnet
- **System Prompt:**
    > "You are a helpful assistant for a Podcast Knowledge Base.
    > Use ONLY the provided context to answer.
    > If the answer is not in the context, say so.
    > CITE SOURCES with [Title - Timestamp]."
- **Input:**
    - User Query
    - Context: Concat(Top 5 Parent Chunks)
- **Output:**
    - Streaming text response.

## 5. Cloud Migration Strategy (Future)

### Database Migration (Chunks)
- **Problem:** SQLite doesn't scale for concurrent writes in cloud.
- **Migration:** Move `podcasts.db` -> **PostgreSQL (e.g., Supabase, Neon)**.
- **Action:**
    - Change `src/db.py` connection string: `sqlite:///podcasts.db` -> `postgresql://user:pass@host/db`.
    - Schema remains identical.

### Vector Migration
- **Problem:** Hosting a local `chroma/` folder in a Docker container is fragile (persistence issues).
- **Migration:** Move Local Chroma -> **Chroma Server** or **Pinecone**.
- **Action:**
    - In `src/embeddings.py`, change:
      ```python
      client = chromadb.PersistentClient(path="chroma_db")
      ```
      to:
      ```python
      client = chromadb.HttpClient(host="my-chroma-server.com")
      # OR switch to Pinecone
      ```

### Compute Migration (Embeddings)
- **Problem:** Generating embeddings on a cheap cloud CPU is slow.
- **Migration:** Move `SentenceTransformer` -> **Embeddings API (OpenAI/Cohere)**.
- **Action:**
    - Replace local model with API call if speed becomes a bottleneck, OR deploy a GPU worker just for ingestion.
