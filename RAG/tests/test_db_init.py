import os
import sqlite3
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import init_db, DB_PATH, get_connection

def test_db_initialization():
    print("Testing Database Initialization...")
    
    # Clean up existing db
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing DB at {DB_PATH}")
    
    # Run init
    init_db()
    
    # Check file exists
    if not os.path.exists(DB_PATH):
        print("FAIL: Database file was not created.")
        return False
        
    # Check tables
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = ['videos', 'transcripts', 'metadata']
    missing = []
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
        if not cursor.fetchone():
            missing.append(table)
            
    conn.close()
    
    if missing:
        print(f"FAIL: Missing tables: {missing}")
        return False
        
    print("SUCCESS: Database initialized with all tables.")
    return True

if __name__ == "__main__":
    test_db_initialization()
