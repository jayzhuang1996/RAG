import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.transcripts import fetch_transcript
from youtube_transcript_api import TranscriptsDisabled

def test_transcript_fetch():
    print("Testing Transcript Fetcher...")
    
    # Use ID found by scraper: "YFjfBk8HI5o"
    test_video_id = "YFjfBk8HI5o" 
    
    print(f"Fetching transcript for video ID: {test_video_id}...")
    
    try:
        raw_data, full_text = fetch_transcript(test_video_id)
        
        if not full_text:
            print("FAIL: Transcript returned empty text.")
            return False
            
        print(f"SUCCESS: Fetched {len(full_text)} characters.")
        print(f"Preview: {full_text[:200]}...")
        return True

    except Exception as e:
        print(f"FAIL: Exception: {e}")
        return False

if __name__ == "__main__":
    test_transcript_fetch()
