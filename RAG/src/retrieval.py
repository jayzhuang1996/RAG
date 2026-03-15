import os
import sys
from rank_bm25 import BM25Okapi
import cohere
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client
from src.embeddings import get_collection, get_embedding_model

load_dotenv()

# Constants
VECTOR_TOP_K = 20
BM25_TOP_K   = 20
RERANK_TOP_N = 5
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

class HybridRetriever:
    """
    Hybrid search: BM25 + (ChromaDB or Supabase) fused via RRF,
    then reranked by Cohere.
    """

    def __init__(self):
        self._bm25_index = None
        self._bm25_corpus = None
        self._cohere_client = None
        self._supabase = get_supabase_client() if USE_SUPABASE else None

    def build_bm25_index(self):
        """Load child chunks from selected DB and build index."""
        if USE_SUPABASE:
            res = self._supabase.table("viking_chunks").select("id, text").eq("type", "child").execute()
            rows = res.data
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, text FROM chunks WHERE type = 'child'")
            rows = cursor.fetchall()
            conn.close()

        self._bm25_corpus = [
            {'id': r['id'], 'tokens': r['text'].lower().split()}
            for r in rows
        ]
        tokenized = [c['tokens'] for c in self._bm25_corpus]
        self._bm25_index = BM25Okapi(tokenized)
        print(f"BM25 index built: {len(self._bm25_corpus)} child chunks.")

    def search_bm25(self, query: str, top_k=BM25_TOP_K):
        if not self._bm25_index:
            self.build_bm25_index()
        tokens = query.lower().split()
        scores = self._bm25_index.get_scores(tokens)
        scored = sorted(
            zip([c['id'] for c in self._bm25_corpus], scores),
            key=lambda x: x[1],
            reverse=True
        )
        return [{'id': chunk_id, 'score': float(score)} for chunk_id, score in scored[:top_k]]

    def search_vector(self, query: str, top_k=VECTOR_TOP_K):
        model = get_embedding_model()
        query_embedding = model.encode([query]).tolist()[0]

        if USE_SUPABASE:
            res = self._supabase.rpc('match_chunks', {
                'query_embedding': query_embedding,
                'match_threshold': 0.1,
                'match_count': top_k
            }).execute()
            return [{'id': r['id'], 'score': r['similarity']} for r in res.data]
        else:
            collection = get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["distances"]
            )
            ids = results['ids'][0]
            scores = [1 / (1 + d) for d in results['distances'][0]]
            return [{'id': chunk_id, 'score': score} for chunk_id, score in zip(ids, scores)]

    def rrf_fusion(self, bm25_results, vector_results, k=60):
        scores = {}
        for rank, item in enumerate(bm25_results):
            scores[item['id']] = scores.get(item['id'], 0.0) + 1.0 / (k + rank + 1)
        for rank, item in enumerate(vector_results):
            scores[item['id']] = scores.get(item['id'], 0.0) + 1.0 / (k + rank + 1)
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [{'id': chunk_id, 'score': score} for chunk_id, score in fused]

    def rerank(self, query: str, fused_results, top_n=RERANK_TOP_N):
        if not fused_results:
            return []
        chunk_ids = [r['id'] for r in fused_results]

        if USE_SUPABASE:
            res = self._supabase.table("viking_chunks").select("id, text").in_("id", chunk_ids).execute()
            chunks_by_id = {r['id']: r['text'] for r in res.data}
        else:
            conn = get_connection()
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(chunk_ids))
            cursor.execute(f"SELECT id, text FROM chunks WHERE id IN ({placeholders})", chunk_ids)
            chunks_by_id = {r['id']: r['text'] for r in cursor.fetchall()}
            conn.close()

        documents = [chunks_by_id.get(cid, '') for cid in chunk_ids]
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY not set.")
        co = cohere.ClientV2(api_key=api_key)
        response = co.rerank(model="rerank-v3.5", query=query, documents=documents, top_n=top_n)
        
        reranked = []
        for result in response.results:
            original_idx = result.index
            reranked.append({
                'id': chunk_ids[original_idx],
                'text': documents[original_idx],
                'score': result.relevance_score
            })
        return reranked

    def get_context(self, reranked_results):
        if not reranked_results:
            return []
        child_ids = [r['id'] for r in reranked_results]

        if USE_SUPABASE:
            res = self._supabase.table("viking_chunks").select("id, parent_id, video_id").in_("id", child_ids).execute()
            child_rows = {r['id']: r for r in res.data}
            parent_ids = list({r['parent_id'] for r in child_rows.values() if r['parent_id']})
            if not parent_ids: return []
            res_p = self._supabase.table("viking_chunks").select("id, text, video_id").in_("id", parent_ids).execute()
            parent_rows = {r['id']: r for r in res_p.data}
        else:
            conn = get_connection()
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(child_ids))
            cursor.execute(f"SELECT id, parent_id, video_id FROM chunks WHERE id IN ({placeholders})", child_ids)
            child_rows = {r['id']: r for r in cursor.fetchall()}
            parent_ids = list({r['parent_id'] for r in child_rows.values() if r['parent_id']})
            if not parent_ids: conn.close(); return []
            placeholders2 = ','.join('?' * len(parent_ids))
            cursor.execute(f"SELECT id, text, video_id FROM chunks WHERE id IN ({placeholders2})", parent_ids)
            parent_rows = {r['id']: dict(r) for r in cursor.fetchall()}
            conn.close()

        context = []
        for res in reranked_results:
            child_id = res['id']
            child_row = child_rows.get(child_id)
            if not child_row: continue
            p_id = child_row['parent_id']
            p_row = parent_rows.get(p_id, {})
            context.append({
                'video_id': child_row['video_id'],
                'parent_id': p_id,
                'parent_text': p_row.get('text', res['text']),
                'child_text': res['text'],
                'child_score': res['score']
            })
        return context

    def retrieve(self, query: str):
        bm25_results = self.search_bm25(query)
        vector_results = self.search_vector(query)
        fused = self.rrf_fusion(bm25_results, vector_results)
        reranked = self.rerank(query, fused)
        return self.get_context(reranked)
