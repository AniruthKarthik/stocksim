import os
import time
import sys
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Global Connection Pool
_pg_pool = None

def init_pool():
    """
    Initializes the global ThreadedConnectionPool using ONLY DATABASE_URL.
    Follows strict positional DSN rules for Supabase compatibility.
    Retries with exponential backoff before failing fatally.
    """
    global _pg_pool
    if _pg_pool is not None:
        return

    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("CRITICAL: DATABASE_URL environment variable is missing.")
        raise RuntimeError("DATABASE_URL is missing — do NOT use defaults.")

    # Clean up DATABASE_URL if it was copied with the key name (common copy-paste error)
    if db_url.startswith("DATABASE_URL="):
        db_url = db_url.split("=", 1)[1].strip("'\" ")
    
    # Safe debugging: log host only to confirm connection target without exposing credentials
    try:
        # Extract host from postgres://user:pass@host:port/db
        db_host = db_url.split('@')[-1].split(':')[0].split('/')[0]
        print(f"INFO: Database host loaded: {db_host}")
    except Exception:
        print("INFO: Database host loaded: [Unable to parse host from DSN]")
    
    # Ensure sslmode=require if it's not already in the URL (critical for Supabase/Render)
    if "sslmode=" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}sslmode=require"

    max_retries = 5
    retry_delay = 2 # Initial delay in seconds

    for attempt in range(1, max_retries + 1):
        try:
            print(f"INFO: Attempting database connection (Attempt {attempt}/{max_retries})...")
            
            # RULE B: Pass DSN POSITIONALLY, NOT as a keyword argument
            _pg_pool = pool.ThreadedConnectionPool(
                1, 
                20, 
                db_url
            )
            
            print("SUCCESS: Database connection pool initialized 🎉")
            return

        except Exception as e:
            print(f"ERROR: Failed to initialize database pool (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            else:
                print("CRITICAL: Could not connect to database after 5 attempts. Exiting app.")
                sys.exit(1)

@contextmanager
def get_db_connection():
    """
    Context manager for getting a connection from the pool.
    Ensures that getconn() is only called if the pool is ready.
    """
    global _pg_pool
    if _pg_pool is None:
        print("CRITICAL: Database pool not initialized. App should have exited during startup.")
        sys.exit(1)
        
    conn = _pg_pool.getconn()
    try:
        yield conn
    finally:
        if _pg_pool:
            _pg_pool.putconn(conn)

def close_pool():
    """
    Closes all connections in the pool.
    """
    global _pg_pool
    if _pg_pool:
        _pg_pool.closeall()
        _pg_pool = None
        print("INFO: Database connection pool closed.")