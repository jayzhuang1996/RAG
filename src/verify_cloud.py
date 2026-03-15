import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set USE_SUPABASE to True for this script
os.environ["USE_SUPABASE"] = "true"

from src.scraper import access_safe_scrape
from src.transcripts import process_video_transcripts
from src.metadata import process_metadata
from src.backfill import backfill_chunks
from src.retrieval import HybridRetriever

def run_verification():
    print("=== Supabase Cloud Verification ===")
    
    # 1. Scrape (limit 1 for testing)
    print("\n[1] Scraping...")
    access_safe_scrape(limit=1)
    
    # 2. Transcripts
    print("\n[2] Processing transcripts...")
    process_video_transcripts(limit=1)
    
    # 3. Backfill (Chunking & Embedding)
    print("\n[3] Backfilling chunks...")
    backfill_chunks(limit=1)
    
    # 4. Metadata
    print("\n[4] Processing metadata...")
    process_metadata(limit=1)
    
    # 5. Retrieval Test
    print("\n[5] Testing retrieval...")
    retriever = HybridRetriever()
    # No need to call build_bm25_index if search_bm25 calls it automatically
    query = "intelligence"
    context = retriever.retrieve(query)
    
    print(f"\nRetrieved {len(context)} results for query '{query}':")
    for i, res in enumerate(context[:3]):
        print(f"[{i+1}] Video: {res['video_id']} | Score: {res['child_score']:.4f}")
        print(f"    Text snippet: {res['parent_text'][:100]}...")

if __name__ == "__main__":
    run_verification()
