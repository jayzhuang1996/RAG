import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client
from src.retrieval import HybridRetriever
from src.agent import run_synthesis_pipeline

load_dotenv()

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

# Singleton retriever — built once, reused for every query
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
        _retriever.build_bm25_index()
    return _retriever

def _build_context_block(context_results):
    if not context_results:
        return "", []

    blocks = []
    sources = []
    video_title_map = {}
    video_to_index = {}
    next_index = 1
    
    if USE_SUPABASE:
        supabase = get_supabase_client()
    else:
        conn = get_connection()
        cursor = conn.cursor()

    for c in context_results:
        video_id = c['video_id']
        
        if video_id not in video_title_map:
            title = video_id
            if USE_SUPABASE:
                res = supabase.table("viking_videos").select("title").eq("id", video_id).execute()
                if res.data: title = res.data[0]['title']
            else:
                cursor.execute("SELECT title FROM videos WHERE id = ?", (video_id,))
                row = cursor.fetchone()
                if row: title = row['title']
            
            video_title_map[video_id] = title
            video_to_index[video_id] = next_index
            sources.append({'index': next_index, 'video_id': video_id, 'title': title, 'text': c['parent_text']})
            next_index += 1
            
        current_idx = video_to_index[video_id]
        blocks.append(f"[Source {current_idx}: {video_title_map[video_id]}]\n{c['parent_text']}")

    if not USE_SUPABASE: conn.close()
    return "\n\n---\n\n".join(blocks), sources

def _build_graph_block(graph_triples):
    if not graph_triples:
        return ""
    
    header = "Verified Relationship Graph Data (Fact Triples):"
    triples_text = "\n".join([f"- {t['subject']} {t['verb']} {t['object']}" for t in graph_triples])
    return f"{header}\n{triples_text}"


import yaml

def get_config_prompt():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'prompts.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('query_system_prompt', "Answer based on context.")

def generate_answer(query: str) -> str:
    """
    Full RAG pipeline: retrieve context → build prompt → call Moonshot → return answer.
    """
    system_prompt = get_config_prompt()
    retriever = get_retriever()

    print("Retrieving relevant context & graph relationships...")
    retrieval_output = retriever.retrieve(query)
    context_results = retrieval_output['text_context']
    graph_triples = retrieval_output['graph_context']

    if not context_results and not graph_triples:
        return {
            "answer": "No relevant content found in the knowledge base for your query.",
            "graph_data": [],
            "sources": []
        }

    context_text, sources = _build_context_block(context_results)
    graph_text = _build_graph_block(graph_triples)

    # Fetch all communities to act as high-level LightRAG context
    community_text = ""
    if USE_SUPABASE:
        try:
            supabase = get_supabase_client()
            com_res = supabase.table("viking_communities").select("title, summary").execute()
            if com_res.data:
                community_text = "MACRO-LEVEL COMMUNITY SUMMARIES:\n" + "\n".join(
                    [f"- {c['title']}: {c['summary']}" for c in com_res.data]
                )
        except Exception as e:
            print(f"Failed to fetch communities: {e}")

    user_message = f"""Context from podcast transcripts:
{context_text}

---
{graph_text}
---
{community_text}

Question: {query}

Answer (cite sources as [Source N]):"""

    moonshot_key = os.getenv("MOONSHOT_API_KEY")
    if not moonshot_key:
        return "Backend Configuration Error: MOONSHOT_API_KEY environment variable is missing."

    # Print sources header
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    print("\nSources retrieved:")
    for s in sources:
        print(f"  [{s['index']}] {s['title']}")

    # Run Multi-Agent Synthesis (LangGraph)
    full_answer = run_synthesis_pipeline(query, context_text, graph_text + "\n" + community_text)
    
    print(f"\n{'='*60}\nFinal Synthesized Answer:\n")
    print(full_answer)
    print(f"\n{'='*60}\n")
    
    return {
        "answer": full_answer,
        "graph_data": graph_triples,
        "sources": sources
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="Your question")
    args = parser.parse_args()
    generate_answer(args.query)
