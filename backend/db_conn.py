import os
import time
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Global Connection Pool
_pg_pool = None

def init_pool():
    global _pg_pool
    if _pg_pool is not None:
        return

    db_url = os.getenv("DATABASE_URL")
    
    # Clean up DATABASE_URL if it was copied with the key name
    if db_url and db_url.startswith("DATABASE_URL="):
        db_url = db_url.split("=", 1)[1].strip("'\" ")

    # Retry configuration
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # Try DSN if it looks like a valid URL
            if db_url and (db_url.startswith("postgres://") or db_url.startswith("postgresql://")):
                safe_url = db_url.split("@")[-1] if "@" in db_url else "URL present"
                print(f"DEBUG: Attempting connection via DSN: {safe_url}")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, db_url, sslmode='require')
            else:
                # Fallback to individual parameters
                host = os.getenv("DB_HOST", "localhost")
                ssl_mode = 'require' if host not in ['localhost', '127.0.0.1'] else 'prefer'
                
                print(f"DEBUG: Using individual connection parameters (host={host}, sslmode={ssl_mode}).")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=host,
                    port=os.getenv("DB_PORT", 5432),
                    sslmode=ssl_mode
                )
            
            print("DB pool initialized successfully 🎉")
            return

        except Exception as e:
            print(f"Error initializing DB pool (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("CRITICAL: Failed to connect to database after retries.")

@contextmanager
def get_db_connection():
    global _pg_pool
    if _pg_pool is None:
        init_pool()
        
    if _pg_pool is None:
        raise Exception("Database pool not initialized. Check logs for connection errors.")
        
    conn = _pg_pool.getconn()
    try:
        yield conn
    finally:
        _pg_pool.putconn(conn)

def close_pool():
    global _pg_pool
    if _pg_pool:
        _pg_pool.closeall()
        print("DB Connection Pool Closed")