import os
import sys
import psycopg2
from psycopg2.extras import execute_values

# Add project root to path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db_conn import get_db_connection

def sync():
    try:
        print("Connecting to local database...")
        with get_db_connection() as local_conn:
            local_cur = local_conn.cursor()
            
            print("Fetching assets and names from local...")
            local_cur.execute("SELECT symbol, name, type FROM assets")
            assets = local_cur.fetchall()
            
            print(f"Found {len(assets)} assets locally.")
            
            # For remote sync, we still need the remote URL
            remote_url = os.getenv("REMOTE_DATABASE_URL")
            if not remote_url:
                print("Error: REMOTE_DATABASE_URL not set in environment.")
                return

            print("Connecting to remote Supabase database...")
            # Use positional DSN for remote too
            remote_conn = psycopg2.connect(remote_url)
            remote_cur = remote_conn.cursor()
            
            print("Updating/Inserting assets on remote...")
            query = """
                INSERT INTO assets (symbol, name, type) 
                VALUES %s 
                ON CONFLICT (symbol) 
                DO UPDATE SET name = EXCLUDED.name, type = EXCLUDED.type
            """
            execute_values(remote_cur, query, assets)
            
            remote_conn.commit()
            print("Sync complete!")
            remote_conn.close()
            
    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == "__main__":
    sync()