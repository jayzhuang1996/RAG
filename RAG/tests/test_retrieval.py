import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.retrieval import HybridRetriever

QUERY = "What did the guest say about AI safety?"

def test_retrieval():
    print("Testing Hybrid Retrieval Pipeline...")
    print(f"Query: '{QUERY}'\n")

    retriever = HybridRetriever()

    # Step 1: Build BM25 index
    print("Building BM25 index...")
    retriever.build_bm25_index()

    # Step 2: BM25 search
    print("\nBM25 search results (top 3):")
    bm25 = retriever.search_bm25(QUERY, top_k=5)
    for r in bm25[:3]:
        print(f"  id={r['id'][:8]}... score={r['score']:.4f}")

    # Step 3: Vector search
    print("\nVector search results (top 3):")
    vec = retriever.search_vector(QUERY, top_k=5)
    for r in vec[:3]:
        print(f"  id={r['id'][:8]}... score={r['score']:.4f}")

    # Step 4: RRF fusion
    print("\nFused results (top 3):")
    fused = retriever.rrf_fusion(bm25, vec)
    for r in fused[:3]:
        print(f"  id={r['id'][:8]}... fused_score={r['score']:.4f}")

    # Step 5: Cohere rerank
    print("\nReranking with Cohere...")
    reranked = retriever.rerank(QUERY, fused)
    print(f"Top {len(reranked)} reranked results:")
    for r in reranked:
        print(f"  id={r['id'][:8]}... relevance={r['score']:.4f}")
        print(f"  text preview: {r['text'][:120]}...")

    # Step 6: Get parent context
    print("\nFetching parent context...")
    context = retriever.get_context(reranked)
    print(f"Retrieved {len(context)} context blocks.")
    for c in context[:2]:
        print(f"\n  video_id={c['video_id']}")
        print(f"  parent_text preview: {c['parent_text'][:200]}...")

    if len(context) > 0:
        print("\nSUCCESS: Full retrieval pipeline working.")
        return True
    else:
        print("\nFAIL: No context returned.")
        return False

if __name__ == "__main__":
    test_retrieval()
