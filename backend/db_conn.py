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

import socket
from urllib.parse import urlparse

# Global Connection Pool
_pg_pool = None

def resolve_to_ipv4(host):
    """Force resolution of a hostname to an IPv4 address."""
    try:
        # AF_INET forces IPv4
        ais = socket.getaddrinfo(host, None, socket.AF_INET)
        if ais:
            return ais[0][4][0]
    except Exception as e:
        print(f"DEBUG: IPv4 resolution failed for {host}: {e}")
    return host

def init_pool():
    global _pg_pool
    if _pg_pool is not None:
        return

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("DATABASE_URL="):
        db_url = db_url.split("=", 1)[1].strip("'\" ")

    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # 1. Try DSN if available
            if db_url and (db_url.startswith("postgres://") or db_url.startswith("postgresql://")):
                parsed = urlparse(db_url)
                host = parsed.hostname
                
                # If we've failed before, try forcing IPv4
                if attempt > 1:
                    ip = resolve_to_ipv4(host)
                    print(f"DEBUG: Retrying with IPv4 address: {ip}")
                    # Reconstruct URL with IP
                    netloc = f"{parsed.username}:{parsed.password}@{ip}:{parsed.port or 5432}"
                    current_url = parsed._replace(netloc=netloc).geturl()
                else:
                    print(f"DEBUG: Attempting connection via DSN to: {host}")
                    current_url = db_url

                _pg_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, current_url, sslmode='require')
            
            # 2. Try individual parameters
            else:
                host = os.getenv("DB_HOST", "localhost")
                if attempt > 1:
                    host = resolve_to_ipv4(host)
                
                ssl_mode = 'require' if host not in ['localhost', '127.0.0.1'] else 'prefer'
                print(f"DEBUG: Using individual parameters (host={host}, sslmode={ssl_mode}).")
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
            err_msg = str(e)
            print(f"Error initializing DB pool (Attempt {attempt + 1}/{max_retries}): {err_msg}")
            
            if "Network is unreachable" in err_msg:
                print("HINT: This usually means the environment doesn't support IPv6. Using the Supabase IPv4 Pooler (port 6543) is highly recommended.")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("CRITICAL: Failed to connect to database after all retries.")

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