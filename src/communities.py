import os
import sys
import json
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
        # Note: In production you might want pagination, assuming <1000 for MVP
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
    # Find all edges between these nodes
    edges = []
    for u in nodes:
        for v in nodes:
            if graph.has_edge(u, v):
                verb = graph[u][v].get('verb', 'connected_to')
                edges.append(f"{u} -> {verb} -> {v}")
    
    # Deduplicate edges
    edges = list(set(edges))
    
    prompt = f"""You are an elite Knowledge Graph architect. 
I have clustered a group of heavily connected entities from podcast transcripts.
Look at the entities and their connections, and provide a broad, thematic 'Title' for this community (e.g. 'Agentic AI Workflows', 'Compute Hardware', 'Venture Capital').
Then write a 2-sentence 'Summary' explaining what this community is about.

Entities: {', '.join(nodes)}

Connections:
{chr(10).join(edges)}

Respond strictly in valid JSON format ONLY:
{{"title": "Thematic Title", "summary": "Two sentence summary."}}
"""
    llm = get_moonshot_llm(temperature=0.2)
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        data = response.content.strip()
        if data.startswith("```json"):
            data = data[7:-3]
        if data.startswith("```"):
            data = data[3:-3]
        return json.loads(data)
    except Exception as e:
        print(f"Failed to parse LLM community JSON: {e}")
        return {"title": "Unknown Community", "summary": "Could not summarize cluster."}

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
    print(f"Found {len(communities)} communities.")

    supabase = get_supabase_client() if USE_SUPABASE else None
    
    if not USE_SUPABASE:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM communities") # Clear old communities
        
    for i, comm in enumerate(communities):
        nodes = list(comm)
        print(f"[{i+1}/{len(communities)}] Summarizing community of size {len(nodes)}...")
        
        info = summarize_cluster(nodes, G)
        title = info['title']
        summary = info['summary']
        
        print(f"   -> Name: {title}")
        
        if USE_SUPABASE:
            supabase.table("viking_communities").insert({
                "title": title,
                "summary": summary,
                "nodes": nodes
            }).execute()
        else:
            cursor.execute("INSERT INTO communities (title, summary, nodes) VALUES (?, ?, ?)", 
                           (title, summary, json.dumps(nodes)))
    
    if not USE_SUPABASE:
        conn.commit()
        conn.close()
        
    print("\n--- LightRAG Community Extraction Complete ---")

if __name__ == "__main__":
    extract_and_save_communities()
