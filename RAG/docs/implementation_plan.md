# Podcast RAG Implementation Plan

## Goal
Build a local, CLI-based Personal Knowledge Base that ingests YouTube podcast transcripts, makes them queryable via natural language using hybrid search and reranking, and provides synthesized answers with citations.

## Architecture Overview

### Layer 1: Data Ingestion (The Foundation)
- **Tools:** `scrapetube` (Channel ID -> Video IDs), `youtube-transcript-api` (Video ID -> Text).
- **Storage:** SQLite (`data/podcasts.db`).
- **Schema:** 
  - `videos` table: `id` (PK), `title`, `channel`, `upload_date`, `url`, `status` (new/processed/error).
  - `transcripts` table: `video_id` (FK), `full_text`, `raw_json` (for timestamps).
- **Logic:**
  - Check SQLite first to avoid re-fetching.
  - Rate limiting (2s sleep) to respect YouTube.
  - "Lightweight Graph" Metadata extraction (Layer 6) happens here: Use Claude Haiku to extract Guests, Topics, Companies per episode.

### Layer 2: Chunking (Parent-Child Strategy)
- **Goal:** Retain context for the LLM (Parent) while enabling precise vector search (Child).
- **Strategy:**
  - **Child Chunk:** 800 tokens, 100 overlap. -> *Vectorized*.
  - **Parent Chunk:** 2400 tokens (mapped to ~3 children). -> *Retrieved for Context*.
- **Storage:**
  - SQLite table `chunks`: `id`, `video_id`, `text`, `type` (parent/child), `parent_id` (FK), `start_time`, `end_time`.

### Layer 3: Embedding & Vector Storage
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (Local, fast, free).
- **Store:** ChromaDB (Persistent local client).
- **Metadata:** `video_id`, `title`, `channel`, `upload_date`, `chunk_index`, `parent_id`, `guests` (list), `companies` (list).
- **Batching:** Process in batches of 50 to manage memory.

### Layer 4: Retrieval (The "Secret Sauce")
- **Hybrid Search:**
  1. **Vector:** ChromaDB query (semantic similarity).
  2. **Keyword:** `rank_bm25` (in-memory index built from SQLite text on startup).
- **Fusion:** RRF (Reciprocal Rank Fusion) to combine top results.
- **Reranking:** Pass top 10 fused results to **Cohere Rerank API**.
- **Refinement:** Select Top 5 reranked chunks.
- **Context Expansion:** Fetch the **Parent Chunks** corresponding to these Top 5 children.

### Layer 5: LLM Synthesis
- **Model:** Anthropic Claude 3.5 Sonnet.
- **Input:** System Prompt + User Query + 5 Parent Chunks (context).
- **System Prompt:** "Answer ONLY using the provided context. Cite sources [Episode Title - Timestamp]."
- **Output:** Streaming response to CLI.

### Layer 6: Meta-Graph (Implemented in Layers 1 & 4)
- **Ingestion:** Haiku extracts metadata.
- **Retrieval:** If query mentions "Sam Altman", filter ChromaDB for `guest=Sam Altman` *before* vector search.

### Layer 7: Semantic Graph (The V2 Upgrade)
- **Goal:** Answer "How did the concept of AI Safety evolve across all episodes?"
- **Mechanism:** Offline batch job extracts "Claims" and "Clusters" (using specialized prompts or Microsoft GraphRAG).
- **Usage:** Retrieve "Community Summaries" instead of just raw text chunks.

---

## Technical Stack
- **Language:** Python 3.10+
- **Database:** SQLite (Relational), ChromaDB (Vector)
- **AI/ML:** 
  - `sentence-transformers` (Embeddings)
  - `anthropic` (Generation & Extraction)
  - `cohere` (Reranking)
- **Utils:** `scrapetube`, `youtube-transcript-api`, `rank_bm25`, `pyyaml`

---

## Evaluation & FAQ

### 1. Critique of Architecture
- **Pros:** 
  - **Parent-Child Chunking** is excellent for podcasts; transcripts are disjointed, so small chunks find the "needle" and large chunks provide the "narrative".
  - **Hybrid + Rerank** is SOTA for RAG. It handles specific terms (BM25) and conceptual questions (Vector) effectively.
  - **No LangChain:** Keeps code debuggable and transparent.
- **Cons:**
  - **In-memory BM25:** If you ingest 1000s of hours, rebuilding BM25 index at startup might take 10-20 seconds. *Mitigation: Pickle the BM25 object or accept startup time for MVP.*
  - **Scraping Fragility:** `scrapetube`/`youtube-transcript-api` depend on YouTube's undocumented frontend. They *will* break eventually. *Mitigation: Good error handling and "skip" logic.*

### 2. Is GraphRAG worth it?
- **For MVP:** **No.** Full GraphRAG (Neo4j, complex traversal) is engineering heavy.
- **Your approach (Layer 6):** Extracting "Entities" (Guests, Companies) as metadata and filtering on them is **80% of the value** for 20% of the cost. It effectively answers "What did Elon Musk say about Mars?" without needing a graph traversal.
- **Upgrade path:** If you simply fail to answer "How are implied themes in Ep 1 related to Ep 50?", then consider graph. For "Lookup" style queries, Metadata filtering is sufficient.

### 3. Path to Production/Agentic
- **Packaging:** The proposed `src/` structure is perfect. Add `pyproject.toml` later to make it `pip install`-able.
- **Agent Integration:** Expose a `query(text) -> answer` function. Agents can just call this tool.
- **Cloud Migration:** 
  - SQLite -> PostgreSQL (RDS/Supabase).
  - Chroma (Local) -> Chroma (Server) or Pinecone/Weaviate.
  - Scraping -> Move to robust scraping APIs (e.g., Apify) as cloud IPs get blocked by YouTube.

---

## Proposed Work Plan

### Phase 1: Setup & Skeleton [Turbo]
- Create folder structure.
- `requirements.txt`.
- `config/channels.yaml`.

### Phase 2: Ingestion Layer (Layer 1 & 6)
- Implement `scraper.py`.
- Implement `transcripts.py` (with SQLite).
- Implement Haiku metadata extraction.

### Phase 3: Embedding & Storage (Layer 2 & 3)
- Implement `embeddings.py` (Chroma + SentenceTransformers).
- Implement Parent-Child logic.

### Phase 4: Retrieval Engine (Layer 4)
- Implement `retrieval.py` (BM25 + Chroma + Cohere).

### Phase 5: Query Interface (Layer 5)
- Implement `query.py` (Sonnet generation).
- CLI `main.py`.

