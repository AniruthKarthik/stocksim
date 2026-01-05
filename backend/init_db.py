import os
import time
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run_sql_file(cursor, filename):
    print(f"INFO: Running {filename}...")
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found.")
        return
    with open(filename, 'r') as f:
        sql = f.read()
        cursor.execute(sql)

def init():
    """
    Initializes the database schema using ONLY DATABASE_URL.
    Retries with exponential backoff before failing fatally.
    """
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("CRITICAL: DATABASE_URL environment variable is missing.")
        sys.exit(1)

    # Clean up DATABASE_URL if it was copied with the key name
    if db_url.startswith("DATABASE_URL="):
        db_url = db_url.split("=", 1)[1].strip("'\" ")
        
    # Ensure sslmode=require
    if "sslmode=" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}sslmode=require"

    max_retries = 5
    retry_delay = 2
    
    conn = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"INFO: Connecting to database to initialize schema (Attempt {attempt}/{max_retries})...")
            # Pass DSN POSITIONALLY
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            # Run schema files
            run_sql_file(cur, "stocksim_schema.sql")
            run_sql_file(cur, "backend/portfolio_schema.sql")
            
            conn.commit()
            print("SUCCESS: Database initialized successfully.")
            return
        except Exception as e:
            print(f"ERROR: Failed to initialize database (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("CRITICAL: Fatal error during database initialization. Exiting.")
                if conn: conn.close()
                sys.exit(1)
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    init()
