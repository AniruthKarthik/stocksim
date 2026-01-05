import os
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run_sql_file(cursor, filename):
    print(f"Running {filename}...")
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found.")
        return
    with open(filename, 'r') as f:
        sql = f.read()
        cursor.execute(sql)

def init():
    """
    Initializes the database schema using DATABASE_URL.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("DATABASE_URL="):
        db_url = db_url.split("=", 1)[1].strip("'\" ")
        
    if not db_url:
        # Fallback construction
        host = os.getenv("DB_HOST", "localhost")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbname = os.getenv("DB_NAME")
        port = os.getenv("DB_PORT", 5432)
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        if host not in ["localhost", "127.0.0.1"]:
            db_url += "?sslmode=require"

    # Retry logic
    max_retries = 5
    retry_delay = 2
    
    conn = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Connecting to database to initialize schema (Attempt {attempt}/{max_retries})...")
            # Positional DSN
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            # Run schema files
            run_sql_file(cur, "stocksim_schema.sql")
            run_sql_file(cur, "backend/portfolio_schema.sql")
            
            conn.commit()
            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"Error initializing DB (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("CRITICAL: Failed to initialize database.")
                if conn: conn.close()
                raise e
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    init()