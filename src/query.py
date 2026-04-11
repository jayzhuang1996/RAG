import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client
from src.retrieval import HybridRetriever

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
    
    if USE_SUPABASE:
        supabase = get_supabase_client()
        # Optimization: Fetch all titles in one go if possible, or just individual lookups for now
    else:
        conn = get_connection()
        cursor = conn.cursor()

    for i, c in enumerate(context_results, start=1):
        video_id = c['video_id']
        title = video_id
        
        if USE_SUPABASE:
            res = supabase.table("viking_videos").select("title").eq("id", video_id).execute()
            if res.data: title = res.data[0]['title']
        else:
            cursor.execute("SELECT title FROM videos WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            if row: title = row['title']

        sources.append({'index': i, 'video_id': video_id, 'title': title})
        blocks.append(f"[Source {i}: {title}]\n{c['parent_text']}")

    if not USE_SUPABASE: conn.close()
    return "\n\n---\n\n".join(blocks), sources

def _build_graph_block(graph_triples):
    if not graph_triples:
        return ""
    
    header = "Verified Relationship Graph Data (Fact Triples):"
    triples_text = "\n".join([f"- {t}" for t in graph_triples])
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
        return "No relevant content found in the knowledge base for your query."

    context_text, sources = _build_context_block(context_results)
    graph_text = _build_graph_block(graph_triples)

    user_message = f"""Context from podcast transcripts:
{context_text}

---
{graph_text}
---

Question: {query}

Answer (cite sources as [Source N]):"""

    moonshot_key = os.getenv("MOONSHOT_API_KEY")
    if not moonshot_key:
        return "Backend Configuration Error: MOONSHOT_API_KEY environment variable is missing."

    client = OpenAI(
        api_key=moonshot_key,
        base_url="https://api.moonshot.ai/v1"
    )

    response = client.chat.completions.create(
        model="moonshot-v1-128k",
        messages=[
            {"role": "system", "system_prompt": system_prompt}, # Note: use system_prompt as content
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        temperature=0.3,
        stream=True  # Stream so it feels responsive
    )

    # Print sources header
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    print("\nSources used:")
    for s in sources:
        print(f"  [{s['index']}] {s['title']}")
    print(f"\n{'='*60}\nAnswer:\n")

    # Stream the response
    full_answer = ""
    for chunk in response:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
        full_answer += delta

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
