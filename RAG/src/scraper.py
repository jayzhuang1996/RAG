import scrapetube
import time
import os
import yaml
from datetime import datetime
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import get_connection, get_supabase_client

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def load_channels():
    # ... (same as before)
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'channels.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['channels']

def get_existing_video_ids():
    """Return a set of video IDs that are already in the chosen DB."""
    if USE_SUPABASE:
        supabase = get_supabase_client()
        res = supabase.table("viking_videos").select("id").execute()
        return {r['id'] for r in res.data}
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM videos")
        existing = {row['id'] for row in cursor.fetchall()}
        conn.close()
        return existing

def fetch_videos_for_channel(channel_url, limit=None):
    # ... (same as before)
    videos = scrapetube.get_channel(channel_url=channel_url)
    results = []
    count = 0
    for video in videos:
        if limit and count >= limit: break
        video_id = video['videoId']
        title = video['title']['runs'][0]['text']
        results.append({'id': video_id, 'title': title})
        count += 1
    return results

def access_safe_scrape(limit=50):
    """Scrape and save to the configured DB (SQLite or Supabase)."""
    channels = load_channels()
    existing_ids = get_existing_video_ids()
    new_videos_count = 0
    
    if USE_SUPABASE:
        supabase = get_supabase_client()
    else:
        conn = get_connection()
        cursor = conn.cursor()
    
    print(f"Loaded {len(channels)} channels. Using {'Supabase' if USE_SUPABASE else 'SQLite'}.")
    
    for channel in channels:
        print(f"Scraping {channel['name']}...")
        found_videos = fetch_videos_for_channel(channel['url'], limit=limit)
        
        for vid in found_videos:
            if vid['id'] not in existing_ids:
                data = {
                    'id': vid['id'],
                    'title': vid['title'],
                    'channel_id': channel['name'],
                    'upload_date': datetime.now().strftime("%Y-%m-%d"),
                    'status': 'new'
                }
                try:
                    if USE_SUPABASE:
                        supabase.table("viking_videos").insert(data).execute()
                    else:
                        cursor.execute("""
                            INSERT INTO videos (id, title, channel_id, upload_date, status)
                            VALUES (?, ?, ?, ?, ?)
                        """, (data['id'], data['title'], data['channel_id'], data['upload_date'], data['status']))
                    new_videos_count += 1
                    existing_ids.add(vid['id'])
                except Exception as e:
                    print(f"Error for {vid['id']}: {e}")
        
        if not USE_SUPABASE: conn.commit()
        time.sleep(1)
        
    if not USE_SUPABASE: conn.close()
    print(f"Scraping complete. Added {new_videos_count} new videos.")

if __name__ == "__main__":
    access_safe_scrape()
