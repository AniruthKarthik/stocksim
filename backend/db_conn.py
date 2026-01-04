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
            _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST", "localhost")
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
