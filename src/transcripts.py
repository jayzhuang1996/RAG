import json
import time
import os
import sys
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def fetch_transcript(video_id):
    # ... (same as before)
    try:
        api = YouTubeTranscriptApi()
        transcript_obj = api.fetch(video_id)
        if hasattr(transcript_obj, 'to_raw_data'):
             raw_data = transcript_obj.to_raw_data()
        elif isinstance(transcript_obj, list):
             raw_data = transcript_obj
        else:
             raw_data = transcript_obj.to_raw_data() # specific fix for current lib
        full_text = " ".join([item['text'] for item in raw_data])
        return raw_data, full_text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        raise Exception(f"Transcripts disabled or not found: {e}")
    except Exception as e:
        raise Exception(f"Error fetching transcript: {e}")

def process_video_transcripts(limit=None):
    """Loop through 'new' videos and fetch their transcripts."""
    if USE_SUPABASE:
        supabase = get_supabase_client()
        res = supabase.table("viking_videos").select("id, title").eq("status", "new").execute()
        videos_to_process = res.data
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM videos WHERE status = 'new'")
        videos_to_process = cursor.fetchall()
    
    print(f"Found {len(videos_to_process)} new videos to process.")
    
    count = 0
    for row in videos_to_process:
        if limit and count >= limit: break
        video_id = row['id']
        title = row['title']
        print(f"Processing: [{video_id}] {title}")
        
        try:
            raw_data, full_text = fetch_transcript(video_id)
            
            if USE_SUPABASE:
                supabase.table("viking_transcripts").upsert({
                    "video_id": video_id,
                    "full_text": full_text,
                    "raw_json": raw_data  # Supabase handles JSONB
                }).execute()
                supabase.table("viking_videos").update({"status": "processed"}).eq("id", video_id).execute()
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO transcripts (video_id, full_text, raw_json)
                    VALUES (?, ?, ?)
                """, (video_id, full_text, json.dumps(raw_data)))
                cursor.execute("UPDATE videos SET status = 'processed' WHERE id = ?", (video_id,))
            print("  -> Success")
            
        except Exception as e:
            print(f"  -> Failed: {e}")
            if USE_SUPABASE:
                supabase.table("viking_videos").update({"status": "error"}).eq("id", video_id).execute()
            else:
                cursor.execute("UPDATE videos SET status = 'error' WHERE id = ?", (video_id,))
            
        if not USE_SUPABASE: conn.commit()
        count += 1
        time.sleep(2)
        
    if not USE_SUPABASE: conn.close()

if __name__ == "__main__":
    process_video_transcripts()
