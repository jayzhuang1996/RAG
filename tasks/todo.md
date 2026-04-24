# Podcast RAG — Current State & Next Steps
_Last updated: 2026-04-23_

---

## WHERE YOU ARE NOW

### Infrastructure (All Green ✅)
- **API:** Live at `zonal-expression-production.up.railway.app` — FastAPI + LangGraph 3-agent pipeline
- **Frontend:** Live at `lightgraph-git-main-jayzhuang9-gmailcoms-projects.vercel.app`
- **Cron:** Railway runs `--step scrape` daily at midnight UTC (discovers new video IDs only)
- **DB:** 22,474 chunks across 44 processed episodes in Supabase

### Channel Coverage (Ground Truth)
| Channel | Status |
|---------|--------|
| Lex Fridman | ✅ 11 episodes processed |
| All-In Podcast | ✅ 12 processed, 1 error |
| Huberman Lab | ✅ 16 episodes processed |
| Joe Rogan | ✅ 10 processed, 1 error |
| PBD Podcast | ✅ 10 processed, 1 error |
| Diary of a CEO | ⚠️ 1 processed, 10 errors (YouTube block) |
| Tucker Carlson | ❌ 11 errors (YouTube block) |
| Modern Wisdom | ❌ 10 errors (YouTube block) |
| My First Million | ❌ 10 errors (YouTube block) |
| Sam Harris | ❌ 10 errors (YouTube block) |
| Theo Von | ❌ 10 errors (YouTube block) |
| Hard Fork | ❌ 5 errors (YouTube block) |

**Root cause of all errors:** YouTube rate-limits transcript fetching by IP after too many requests in quick succession. Run `python src/ingest.py --step transcript` again tomorrow with a fresh IP session to clear them.

---

## KNOWN ISSUES
- [ ] `viking_health` table missing in Supabase — health monitor logs fail silently (cosmetic only)
- [ ] Cohere Trial key hits 100k token/min rate limit on large embed batches — retries work but slow
- [ ] 6 new channels have zero processed content — need IP cooldown before retrying transcripts

---

## NEXT STEPS (Prioritized)

### Priority 1 — Fill the Database (Do Tomorrow)
```bash
# Run after a few hours cooldown on YouTube IP
python src/ingest.py --step transcript
python src/ingest.py --step embed
```
This will unblock Tucker, Modern Wisdom, Sam Harris, Theo Von, My First Million, Hard Fork.
Target: ~80+ processed episodes, ~40,000+ chunks.

### Priority 2 — Decide the Product Direction
**Option A: Personal intelligence tool** → No further dev needed. Use as-is.
**Option B: Product/Demo for clients** → Need landing page, auth, curated sample queries, pitch deck.

### Priority 3 — Upgrade Cohere to Production Key
Current trial key hits rate limits on embed batches. At $0-20/mo production tier,
embedding becomes instant and reliable.
https://dashboard.cohere.com/api-keys

### Priority 4 — (If Product) Rebuild Frontend as Demo
- Clean landing page: one-sentence value prop
- 5-6 curated demo queries that show off peak output
- Remove technical UI chrome (pipeline status labels, etc.)
- Add share/export for briefings

### Priority 5 — Cohere Prod Key + Upgrade Rerank Model
Swap `rerank-english-v2.0` → `rerank-english-v3.0` for better retrieval quality.

---

## COMPLETED (Archived)
- [x] SQLite → Supabase cloud migration
- [x] PyTorch/SentenceTransformers → Cohere API (removed 1.5GB from container)
- [x] BM25 in-memory index removed (prevented 500MB OOM crashes)
- [x] LangGraph 3-agent pipeline (Researcher → Analyst → Writer)
- [x] LightRAG community summaries injected as macro context
- [x] Railway split into 2 services: API (24/7) + Cron (scrape only)
- [x] 11 channels configured in `config/channels.yaml`
- [x] Per-channel scrape errors made non-fatal
- [x] Vercel redeployed pointing to new Railway API URL
