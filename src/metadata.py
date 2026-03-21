import os
import sys
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client

load_dotenv()

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

ALLOWED_VERBS = [
    "works_at", "founded", "co_founded", "left", "advises",
    "mentors", "criticizes", "collaborated_with", "disagrees_with",
    "advocates_for", "warns_against", "researches",
    "primarily_covers", "briefly_mentions"
]

def _get_client():
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        raise ValueError("Backend Configuration Error: MOONSHOT_API_KEY environment variable is missing.")
    return OpenAI(api_key=api_key, base_url="https://api.moonshot.ai/v1")

def extract_metadata(text):
    client = _get_client()
    truncated_text = text[:25000]
    allowed_verbs_str = ", ".join(ALLOWED_VERBS)

    prompt = f"""
You are a metadata and relationship extraction engine for podcasts.
Analyze the following podcast transcript and extract:
1. ENTITIES: guests, topics, companies.
2. RELATIONSHIPS using ONLY these verbs: [{allowed_verbs_str}]

Return ONLY valid JSON:
{{
  "guests": ["Name"],
  "topics": ["Topic 1"],
  "companies": ["Company A"],
  "relationships": [{{"subject": "...", "verb": "...", "object": "..."}}]
}}
Transcript:
{truncated_text}
"""
    try:
        completion = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=[
                {"role": "system", "content": "You are a structured data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        if "relationships" in data:
            data["relationships"] = [
                r for r in data["relationships"]
                if isinstance(r, dict) and r.get("verb") in ALLOWED_VERBS
            ]
        return data
    except Exception as e:
        print(f"Error: {e}")
        return {"guests": [], "topics": [], "companies": [], "relationships": []}

def process_metadata(limit=None):
    if USE_SUPABASE:
        supabase = get_supabase_client()
        res_t = supabase.table("viking_transcripts").select("video_id, full_text").execute()
        res_m = supabase.table("viking_metadata").select("video_id").execute()
        processed_ids = {r['video_id'] for r in res_m.data}
        videos_to_process = [r for r in res_t.data if r['video_id'] not in processed_ids]
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT t.video_id, t.full_text FROM transcripts t WHERE t.video_id NOT IN (SELECT DISTINCT video_id FROM metadata)")
        videos_to_process = cursor.fetchall()

    for row in videos_to_process:
        if limit and limit <= 0: break
        video_id = row['video_id']
        text = row['full_text']
        try:
            data = extract_metadata(text)
            if USE_SUPABASE:
                rows = []
                for g in data.get('guests', []): rows.append({"video_id": video_id, "type": "guest", "value": g})
                for t in data.get('topics', []): rows.append({"video_id": video_id, "type": "topic", "value": t})
                for c in data.get('companies', []): rows.append({"video_id": video_id, "type": "company", "value": c})
                if rows: supabase.table("viking_metadata").insert(rows).execute()
                
                rel_rows = []
                for rel in data.get('relationships', []):
                    rel_rows.append({"video_id": video_id, "subject": rel['subject'], "verb": rel['verb'], "object": rel['object']})
                if rel_rows: supabase.table("viking_relationships").insert(rel_rows).execute()
            else:
                for g in data.get('guests', []): cursor.execute("INSERT INTO metadata (video_id, type, value) VALUES (?, 'guest', ?)", (video_id, g))
                # ... other sqlite logic
                conn.commit()
            if limit: limit -= 1
        except Exception as e:
            print(f"Error: {e}")
    if not USE_SUPABASE: conn.close()

if __name__ == "__main__":
    process_metadata()
