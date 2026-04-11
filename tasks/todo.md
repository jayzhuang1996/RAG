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
- [x] Implement `src/graph_viz.py` (Relationship "Drawing" - Mermaid/JSON output)
- [x] Add `main.py graph` command
- [x] Externalize `SYSTEM_PROMPT` to `config/prompts.yaml` for user customization

## 5. Phase 9: Cloud Migration & Railway Setup [IN PROGRESS]
- [x] Refactor core scripts (`db.py`, `embeddings.py`, `retrieval.py`, etc.) for Supabase
- [x] Finalize Supabase Schema (Ensure `viking_metadata` and `match_chunks` RPC exist)
- [x] Run Full Data Migration (`src/migrate_to_cloud.py`)
- [x] Create Dockerfile, railway.json, and api.py
- [x] Prepare and commit Git repository
- [x] Integrate full ingestion pipeline (1-4) in `src/ingest.py`
- [x] Deploy Query API to **Railway** (FastAPI) — verified live
- [ ] **CRITICAL: Set up Railway Cron for Ingestion Worker**
  - Go to Railway → Ingester Service → Settings
  - Custom Start Command: `python src/ingest.py --limit 10`
  - Cron Schedule: `0 0 * * *` (midnight UTC daily)
  - Ensure all env vars are copied from the API service

## 6. Phase 11: Graph-Augmented Generation [DONE]
- [x] Upgrade `src/query.py` to auto-detect entities from user query
- [x] Fetch all Subject/Verb/Object triples for those entities from `viking_relationships`
- [x] Inject graph relationships as a structured block into the Moonshot AI context
- [x] Update `api.py` to return graph data alongside the text answer (for frontend to render)
- [x] Push to Railway → auto-deploy

## 7. Phase 10: Simple Frontend (Next.js on Vercel) [PLANNED]
- [ ] Initialize Next.js project
- [ ] Build Chat/Search Interface (streaming text response)
- [ ] Integrate D3.js/Mermaid.js for **live relationship graph** shown alongside each answer
- [ ] Hierarchical drillable subgraph (click a node to expand its connections)
- [ ] **Vercel Setup & Deployment**
  - Connect GitHub repository to Vercel dashboard
  - Configure Environment Variables (point to Railway API URL)
  - Deploy and test end-to-end integration

## 8. Final End-to-End Verification
- [ ] Run full pipeline from cloud ingestion to frontend query with live graph visualization
