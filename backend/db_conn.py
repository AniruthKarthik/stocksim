import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Global Connection Pool
# Min 1, Max 20 connections.
# This avoids the overhead of handshake for every request.
_pg_pool = None

def init_pool():
    global _pg_pool
    if _pg_pool is None:
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                # Use the single connection string (DSN)
                print(f"DEBUG: Connecting to DB using DATABASE_URL (Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'Unknown'})")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dsn=database_url,
                    sslmode=os.getenv("DB_SSLMODE", "require") 
                )
            else:
                # Fallback to individual credentials
                host = os.getenv("DB_HOST", "localhost")
                print(f"DEBUG: Connecting to DB (Host: {host})")
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", "5432"),
                    sslmode=os.getenv("DB_SSLMODE", "prefer")
                )
            print("DB Connection Pool Initialized")
        except Exception as e:
            print(f"Error initializing DB pool: {e}")

@contextmanager
def get_db_connection():
    """
    Yields a connection from the pool.
    Usage:
        with get_db_connection() as conn:
            cur = conn.cursor()
            ...
    """
    global _pg_pool
    if _pg_pool is None:
        init_pool()
        
    if _pg_pool is None:
        raise Exception("Database connection pool failed to initialize. Check your database credentials and connection.")

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
