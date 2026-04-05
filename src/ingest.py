import argparse
import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import access_safe_scrape
from src.transcripts import process_video_transcripts
from src.metadata import process_metadata
from src.backfill import backfill_chunks
from src.db import get_supabase_client

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

def _record_health(status, error=None, videos_processed=0):
    """Write a health status row to Supabase for monitoring."""
    if not USE_SUPABASE:
        return
    try:
        supabase = get_supabase_client()
        payload = {
            "job": "ingestion",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "videos_processed": videos_processed,
            "error_message": str(error) if error else None,
        }
        if status == "success":
            payload["last_success"] = datetime.now(timezone.utc).isoformat()
        supabase.table("viking_health").upsert(payload).execute()
    except Exception as e:
        print(f"[Health Monitor] Failed to write health status: {e}")

def main():
    parser = argparse.ArgumentParser(description="Ingest podcast data (Scrape -> Transcript -> Metadata -> Embed)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of videos to process per step")
    parser.add_argument("--step", type=str, choices=['all', 'scrape', 'transcript', 'metadata', 'embed'], default='all', help="Run specific step or all")

    args = parser.parse_args()

    print("=== Starting Ingestion Pipeline ===")
    _record_health("running")

    try:
        # 1. Scrape
        if args.step in ['all', 'scrape']:
            print("\n--- Step 1: Scraping Channels ---")
            limit = args.limit if args.limit else 50
            access_safe_scrape(limit=limit)

        # 2. Transcripts
        if args.step in ['all', 'transcript']:
            print("\n--- Step 2: Fetching Transcripts ---")
            process_video_transcripts(limit=args.limit)

        # 3. Metadata
        if args.step in ['all', 'metadata']:
            print("\n--- Step 3: Extracting Metadata (Moonshot AI) ---")
            process_metadata(limit=args.limit)

        # 4. Embed (Backfill)
        if args.step in ['all', 'embed']:
            print("\n--- Step 4: Chunking & Embedding (Vector DB) ---")
            backfill_chunks(limit=args.limit)

        print("\n=== Pipeline Complete ===")
        _record_health("success", videos_processed=args.limit or 0)

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        _record_health("failed", error=e)
        raise  # still exit with non-zero code so Railway shows it as a failed run

if __name__ == "__main__":
    main()
