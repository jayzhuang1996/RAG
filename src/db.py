from supabase import create_client, Client
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

# Path to database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'podcasts.db')

def get_connection():
    """Get a connection to the SQLite database (Local Legacy)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_supabase_client() -> Client:
    """Get a Supabase client (Cloud Native)."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(url, key)

def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Videos Table
    # Stores metadata about each video found in the channels
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        channel_id TEXT NOT NULL,
        upload_date TEXT,
        url TEXT,
        status TEXT DEFAULT 'new' CHECK(status IN ('new', 'processed', 'error'))
    );
    """)

    # 2. Transcripts Table
    # Stores the raw and processed text
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        video_id TEXT PRIMARY KEY,
        full_text TEXT,
        raw_json TEXT,  -- JSON string of raw transcript with timestamps
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
    );
    """)
    
    # 3. Metadata Table (Layer 6)
    # Stores extracted guests and topics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('guest', 'topic', 'company')),
        value TEXT NOT NULL,
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
    );
    """)

    # 4. Chunks Table (Layer 2)
    # Stores parent and child chunks for RAG
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,          -- UUID
        video_id TEXT NOT NULL,
        text TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('parent', 'child')),
        parent_id TEXT,               -- NULL for parent chunks, FK to chunks(id) for children
        start_time REAL,              -- Timestamp in seconds
        end_time REAL,
        chunk_index INTEGER,          -- Order within the video
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES chunks(id) ON DELETE CASCADE
    );
    """)

    # 5. Relationships Table (Full Lightweight GraphRAG)
    # Stores typed triples: (subject, verb, object) extracted from transcripts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        verb TEXT NOT NULL,
        object TEXT NOT NULL,
        FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
    );
    """)

    # 6. Communities Table (LightRAG / Phase 12)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS communities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        nodes TEXT NOT NULL -- Stored as JSON string locally
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
