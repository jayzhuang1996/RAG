#!/usr/bin/env python3
"""
Podcast RAG - Main CLI Entry Point

Usage:
  python main.py ingest [--limit N] [--step all|scrape|transcript|metadata]
  python main.py query "What did Sam Altman say about AI safety?"
  python main.py backfill [--limit N]
"""

import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def cmd_ingest(args):
    from src.ingest import main as ingest_main
    sys.argv = ['ingest']
    if args.limit:
        sys.argv += ['--limit', str(args.limit)]
    if args.step:
        sys.argv += ['--step', args.step]
    ingest_main()

def cmd_backfill(args):
    from src.backfill import backfill_chunks
    backfill_chunks(limit=args.limit)

def cmd_query(args):
    from src.query import generate_answer
    generate_answer(args.question)

def cmd_graph(args):
    from src.graph_viz import generate_mermaid_graph
    graph = generate_mermaid_graph(video_id=args.video_id, subject=args.subject)
    print("\n--- Relationship Graph (Mermaid Format) ---\n")
    print(graph)
    print("\n--- End Graph ---\n")

def main():
    parser = argparse.ArgumentParser(
        description="Podcast RAG — Ingest and Query your podcast knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest the 50 most recent videos from all channels in config
  python main.py ingest --limit 50

  # Only run the transcript step
  python main.py ingest --step transcript

  # Embed/chunk all transcripts that don't have vectors yet
  python main.py backfill

  # Ask a question
  python main.py query "What did Sam Altman say about AI safety?"
        """
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # --- ingest ---
    ingest_parser = subparsers.add_parser('ingest', help='Scrape, transcribe, and extract metadata')
    ingest_parser.add_argument('--limit', type=int, default=None, help='Max videos per step')
    ingest_parser.add_argument('--step', choices=['all', 'scrape', 'transcript', 'metadata'], default='all')

    # --- backfill ---
    backfill_parser = subparsers.add_parser('backfill', help='Chunk and embed existing transcripts')
    backfill_parser.add_argument('--limit', type=int, default=None)

    # --- query ---
    query_parser = subparsers.add_parser('query', help='Ask a question against your knowledge base')
    query_parser.add_argument('question', type=str, help='Your question in quotes')

    # --- graph ---
    graph_parser = subparsers.add_parser('graph', help='Visualize relationships from the knowledge base')
    graph_parser.add_argument('--video_id', help='Filter by video ID')
    graph_parser.add_argument('--subject', help='Filter by subject name')

    args = parser.parse_args()

    if args.command == 'ingest':
        cmd_ingest(args)
    elif args.command == 'backfill':
        cmd_backfill(args)
    elif args.command == 'query':
        cmd_query(args)
    elif args.command == 'graph':
        cmd_graph(args)

if __name__ == "__main__":
    main()
