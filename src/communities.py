import os
import sys
import json
import time
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def get_moonshot_llm(temperature=0.3):
    return ChatOpenAI(
        model="moonshot-v1-128k",
        api_key=os.environ.get("MOONSHOT_API_KEY"),
        base_url="https://api.moonshot.ai/v1",
        temperature=temperature
    )

def fetch_all_relationships():
    relations = []
    if USE_SUPABASE:
        supabase = get_supabase_client()
        res = supabase.table("viking_relationships").select("subject,verb,object").execute()
        relations = res.data
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject, verb, object FROM relationships")
        for row in cursor.fetchall():
            relations.append({"subject": row["subject"], "verb": row["verb"], "object": row["object"]})
        conn.close()
    return relations

def summarize_cluster(nodes: list, graph: nx.Graph) -> dict:
    """Takes a list of nodes in a community, looks at their internal edges, and uses LLM to name/summarize it."""
    edges = []
    for u in nodes:
        for v in nodes:
            if graph.has_edge(u, v):
                verb = graph[u][v].get('verb', 'connected_to')
                edges.append(f"{u} -> {verb} -> {v}")
    edges = list(set(edges))

    prompt = f"""You are a Strategic Intelligence Analyst for a top-tier venture fund.
I have clustered a group of heavily connected entities from recent high-signal podcast transcripts (Lex Fridman, All-In, Huberman, etc.).

Your task is to analyze this 'cluster' and provide a Strategic Intelligence Briefing.

Entities: {', '.join(nodes)}

Connections observed in the Graph:
{chr(10).join(edges)}

Respond STRICTLY in valid JSON format ONLY:
{{
  "title": "A punchy, editorial headline (e.g., 'The GPU Arms Race' or 'The Emergence of Agentic OS')",
  "summary": "A 1-sentence macro-summary of the cluster's relevance.",
  "insight": "High-level strategic 'So-What'. Why should a business leader care about this specific grouping of entities right now?",
  "tensions": "What are the major disagreements or technical hurdles mentioned between these entities?",
  "top_entities": ["The 3-5 most influential entities in this cluster"]
}}
"""
    llm = get_moonshot_llm(temperature=0.2)

    # Retry with exponential backoff for Moonshot's 20 RPM rate limit
    for attempt in range(4):
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            data = response.content.strip()
            if data.startswith("```json"):
                data = data[7:-3]
            if data.startswith("```"):
                data = data[3:-3]
            return json.loads(data)
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                wait = 4 ** attempt  # 1s, 4s, 16s, 64s
                print(f"   [Rate Limit] Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                print(f"   Failed to summarize cluster: {e}")
                return {"title": "Unknown Community", "summary": "Could not summarize cluster."}

    return {"title": "Unknown Community", "summary": "Rate limit exceeded after retries."}

def extract_and_save_communities():
    print("Fetching relationships...")
    relations = fetch_all_relationships()
    if not relations:
        print("No relationships found. Run ingest first.")
        return

    print(f"Building network graph with {len(relations)} edges...")
    G = nx.Graph()
    for rel in relations:
        s, v, o = rel['subject'], rel['verb'], rel['object']
        G.add_edge(s, o, verb=v)

    print(f"Graph built. Modularity clustering nodes...")
    communities = list(greedy_modularity_communities(G))
    # Sort by size descending
    communities.sort(key=len, reverse=True)
    # Target only the top 12 most significant macro-clusters
    communities = communities[:12]
    print(f"Kept top {len(communities)} most significant communities.")

    supabase = get_supabase_client() if USE_SUPABASE else None

    if USE_SUPABASE:
        print("Clearing old communities from Supabase...")
        supabase.table("viking_communities").delete().neq("id", -1).execute()
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM communities")

    for i, comm in enumerate(communities):
        nodes = list(comm)
        print(f"[{i+1}/{len(communities)}] Summarizing community of size {len(nodes)}...")

        info = summarize_cluster(nodes, G)
        title = info.get('title', 'Unknown Cluster')
        
        # Pack rich metadata into the summary field since we have schema rigidity
        rich_data = {
            "summary": info.get('summary', ''),
            "insight": info.get('insight', ''),
            "tensions": info.get('tensions', ''),
            "top_entities": info.get('top_entities', [])
        }
        summary_str = json.dumps(rich_data)
        
        print(f"   -> Name: {title}")

        if USE_SUPABASE:
            supabase.table("viking_communities").insert({
                "title": title,
                "summary": summary_str,
                "nodes": nodes
            }).execute()
        else:
            cursor.execute("INSERT INTO communities (title, summary, nodes) VALUES (?, ?, ?)",
                           (title, summary_str, json.dumps(nodes)))

        # Wait 4s between each cluster to respect Moonshot's 20 RPM limit
        time.sleep(4)

    if not USE_SUPABASE:
        conn.commit()
        conn.close()

    print("\n--- LightRAG Community Extraction Complete ---")

if __name__ == "__main__":
    extract_and_save_communities()
