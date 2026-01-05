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
    
    # Retry configuration
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            if db_url:
                # Mask password for safe logging
                safe_url = db_url.split("@")[-1] if "@" in db_url else "URL present but hidden"
                print(f"DEBUG: Connecting using DATABASE_URL to: {safe_url}")
                
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    1, 20, db_url, sslmode='require'
                )
            else:
                print("DEBUG: DATABASE_URL not found. Falling back to individual parameters.")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", 5432)
                )
            
            print("DB pool initialized successfully 🎉")
            return # Success!

        except Exception as e:
            print(f"Error initializing DB pool (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("CRITICAL: Failed to connect to database after retries.")
                # We don't raise here to allow the app to start, 
                # but DB calls will fail until pool is fixed (or app restarts).

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