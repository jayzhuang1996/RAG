from youtube_transcript_api import YouTubeTranscriptApi
import json

video_id = "YFjfBk8HI5o"

print("--- Testing API instantiation ---")
try:
    api = YouTubeTranscriptApi()
    res = api.fetch(video_id)
    print(f"Result type: {type(res)}")
    print(f"Dir(res): {dir(res)}")
    
    # Try common attributes if present
    if hasattr(res, 'fetch'):
        print("Attempting .fetch() on object...")
        try:
            data = res.fetch()
            print(f"Sub-fetch result type: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"First item: {data[0]}")
        except Exception as e:
            print(f"Sub-fetch failed: {e}")

    # Inspect if list-like
    try:
        if isinstance(res, list):
            pass # Already checked
        else:
            # Maybe iterable?
            pass
    except: pass
except Exception as e:
    print(f"Error: {e}")
