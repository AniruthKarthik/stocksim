import os
import time
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Global Connection Pool
_pg_pool = None

def init_pool():
    """
    Initializes the global ThreadedConnectionPool with retry logic.
    Follows strict positional DSN rules for Supabase compatibility.
    """
    global _pg_pool
    if _pg_pool is not None:
        return

    db_url = os.getenv("DATABASE_URL")
    
    # Clean up DATABASE_URL if it was copied with the key name
    if db_url and db_url.startswith("DATABASE_URL="):
        db_url = db_url.split("=", 1)[1].strip("'\" ")
    
    # Ensure sslmode=require if it's a remote connection and not specified
    if db_url and "sslmode=" not in db_url and "localhost" not in db_url and "127.0.0.1" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}sslmode=require"

    max_retries = 5
    retry_delay = 2 # Initial delay in seconds

    for attempt in range(1, max_retries + 1):
        try:
            if db_url:
                # RULE B: Pass DSN POSITIONALLY
                print(f"DEBUG: Attempting DB connection (Attempt {attempt}/{max_retries})...")
                _pg_pool = pool.ThreadedConnectionPool(
                    1, 
                    20, 
                    db_url
                )
            else:
                # Fallback to individual parameters only if DATABASE_URL is missing
                print(f"DEBUG: DATABASE_URL missing, falling back to individual parameters (Attempt {attempt}/{max_retries})...")
                host = os.getenv("DB_HOST", "localhost")
                user = os.getenv("DB_USER")
                password = os.getenv("DB_PASSWORD")
                dbname = os.getenv("DB_NAME")
                port = os.getenv("DB_PORT", 5432)
                
                # Construct DSN from parameters
                constructed_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
                if host not in ["localhost", "127.0.0.1"]:
                    constructed_url += "?sslmode=require"
                
                _pg_pool = pool.ThreadedConnectionPool(1, 20, constructed_url)
            
            print("DB pool initialized successfully 🎉")
            return

        except Exception as e:
            print(f"Error initializing DB pool (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            else:
                print("CRITICAL: Failed to connect to database after 5 attempts.")
                _pg_pool = None

@contextmanager
def get_db_connection():
    """
    Context manager for getting a connection from the pool.
    """
    global _pg_pool
    if _pg_pool is None:
        init_pool()
        
    if _pg_pool is None:
        raise RuntimeError("Database pool not initialized. Check logs for connection errors.")
        
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
        print("DB Connection Pool Closed")
