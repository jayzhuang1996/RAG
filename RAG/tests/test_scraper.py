import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import fetch_videos_for_channel

def test_scraper_logic():
    print("Testing Scraper Logic...")
    
    # Lex Fridman Channel URL (from config)
    channel_url = "https://www.youtube.com/@lexfridman"
    
    print(f"Fetching 5 videos from {channel_url}...")
    try:
        videos = fetch_videos_for_channel(channel_url, limit=5)
        
        if not videos:
            print("FAIL: No videos returned.")
            return False
            
        print(f"SUCCESS: Found {len(videos)} videos:")
        for v in videos:
            print(f" - [{v['id']}] {v['title']}")
            
        return True
    except Exception as e:
        print(f"FAIL: Scraper threw exception: {e}")
        return False

if __name__ == "__main__":
    test_scraper_logic()
