import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection

def generate_mermaid_graph(video_id=None, subject=None):
    """
    Fetches relationships from the DB and formats them as a Mermaid diagram.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT subject, verb, object FROM relationships"
    params = []
    
    if video_id:
        query += " WHERE video_id = ?"
        params.append(video_id)
    elif subject:
        query += " WHERE subject LIKE ?"
        params.append(f"%{subject}%")
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "No relationships found for the given criteria."
        
    mermaid = ["graph TD"]
    for row in rows:
        # Sanitize for Mermaid labels
        s = row['subject'].replace(' ', '_').replace('"', '')
        v = row['verb'].replace(' ', '_')
        o = row['object'].replace(' ', '_').replace('"', '')
        mermaid.append(f"    {s} -- {v} --> {o}")
        
    return "\n".join(mermaid)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_id", help="Filter by video ID")
    parser.add_argument("--subject", help="Filter by subject name")
    args = parser.parse_args()
    
    print("\n--- Relationship Graph (Mermaid Format) ---\n")
    print(generate_mermaid_graph(video_id=args.video_id, subject=args.subject))
    print("\n--- End Graph ---\n")
