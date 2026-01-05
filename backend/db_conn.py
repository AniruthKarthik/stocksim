import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Global Connection Pool
_pg_pool = None

def init_pool():
    global _pg_pool
    if _pg_pool is None:
        try:
            # Prefer DATABASE_URL (Connection String)
            db_url = os.getenv("DATABASE_URL")
            
            if db_url:
                print("DEBUG: Connecting using DATABASE_URL")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    1, 20, dsn=db_url
                )
            else:
                print("DEBUG: Connecting using individual parameters")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", 5432)
                )
            print("DB Connection Pool Initialized Successfully")
        except Exception as e:
            print(f"Error initializing DB pool: {e}")

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