import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import access_safe_scrape
from src.transcripts import process_video_transcripts
from src.metadata import process_metadata
from src.backfill import backfill_chunks

def main():
    parser = argparse.ArgumentParser(description="Ingest podcast data (Scrape -> Transcript -> Metadata -> Embed)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of videos to process per step")
    parser.add_argument("--step", type=str, choices=['all', 'scrape', 'transcript', 'metadata', 'embed'], default='all', help="Run specific step or all")
    
    args = parser.parse_args()
    
    print("=== Starting Ingestion Pipeline ===")
    
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

if __name__ == "__main__":
    main()
