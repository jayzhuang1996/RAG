# Podcast RAG - Technical Backbone TODO

## 1. Governance & Agent Rules [DONE]
- [x] Import `.cursorrules` from Stocks project
- [x] Codify permanent reasoning loop in `antigravity.md`
- [x] Initialize `tasks/todo.md` and `tasks/lessons.md`

## 2. Phase 1-5 Core System [DONE & VERIFIED]
- [x] SQLite Schema & DB Infrastructure
- [x] YouTube Scraper & Transcript Engine
- [x] Moonshot AI Metadata Extraction
- [x] Parent-Child Chunking Strategy
- [x] MiniLM Embedding & ChromaDB Storage
- [x] Hybrid Retriever (BM25 + Vector + RRF + Cohere Rerank)

## 3. Phase 6: Query Interface [DONE]
- [x] Implement `src/query.py` (Moonshot AI Answer Synthesis)
- [x] Citations: `[Source N]` format with episode titles
- [x] Streaming response implementation
- [x] Implement `main.py` CLI

## 4. Phase 8: GraphRAG & Visualization [IN PROGRESS]
- [ ] Implement `src/graph_viz.py` (Relationship "Drawing" - Mermaid/JSON output)
- [ ] Add `main.py graph` command
- [ ] Externalize `SYSTEM_PROMPT` to `config/prompts.yaml` for user customization

## 5. Phase 9: Cloud Migration & Railway Setup (CRITICAL) [IN PROGRESS]
- [x] Refactor core scripts (`db.py`, `embeddings.py`, `retrieval.py`, etc.) for Supabase
- [x] Finalize Supabase Schema (Ensure `viking_metadata` and `match_chunks` RPC exist)
- [x] Run Full Data Migration (`src/migrate_to_cloud.py`)
- [x] Create Dockerfile, railway.json, and api.py
- [x] Prepare and commit Git repository
- [ ] Deploy Ingestion Worker to **Railway** (Scheduled CRON)
- [ ] Deploy Query API to **Railway** (FastAPI)

## 6. Phase 10: Simple Frontend (Next.js on Vercel) [PAUSED]
- [ ] Initialize Next.js project
- [ ] Build Chat/Search Interface
- [ ] Integrate Mermaid.js for relationship visualization
- [ ] Deploy to Vercel

## 7. Final End-to-End Verification
- [ ] Run full pipeline from cloud ingestion to frontend query
