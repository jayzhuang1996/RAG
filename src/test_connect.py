import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_connectivity():
    print("=== Connectivity Smoke Test ===")
    
    # 1. Test Supabase URL resolution
    supabase_url = os.getenv("SUPABASE_URL")
    print(f"Testing Supabase URL: {supabase_url}")
    try:
        res = requests.head(supabase_url, timeout=5)
        print(f"Supabase reachability: SUCCESS (Status: {res.status_code})")
    except Exception as e:
        print(f"Supabase reachability: FAILED - {e}")

    # 2. Test Moonshot API resolution
    moonshot_url = "https://api.moonshot.ai/v1/models"
    print(f"Testing Moonshot URL: {moonshot_url}")
    try:
        res = requests.head(moonshot_url, timeout=5)
        print(f"Moonshot reachability: SUCCESS (Status: {res.status_code})")
    except Exception as e:
        print(f"Moonshot reachability: FAILED - {e}")

if __name__ == "__main__":
    test_connectivity()
