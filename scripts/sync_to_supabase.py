
import psycopg2
import os
from psycopg2.extras import execute_values

# Source (Local)
LOCAL_DB = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

# Target (Supabase - from .env)
# The user should ensure their .env has the Supabase credentials 
# or they can set them as environment variables.
REMOTE_DB = {
    "dbname": os.getenv("REMOTE_DB_NAME", "postgres"),
    "user": os.getenv("REMOTE_DB_USER", "postgres"),
    "password": os.getenv("REMOTE_DB_PASSWORD", ""),
    "host": os.getenv("REMOTE_DB_HOST", "db.njafvtezrrkekdddcpoc.supabase.co"),
    "port": os.getenv("REMOTE_DB_PORT", "5432")
}

def sync():
    try:
        print("Connecting to local database...")
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor()
        
        print("Fetching assets and names from local...")
        local_cur.execute("SELECT symbol, name, type FROM assets")
        assets = local_cur.fetchall()
        
        print(f"Found {len(assets)} assets locally.")
        
        print("Connecting to remote Supabase database...")
        # Note: Added sslmode=require for Supabase
        remote_conn = psycopg2.connect(**REMOTE_DB, sslmode='require')
        remote_cur = remote_conn.cursor()
        
        print("Updating/Inserting assets on remote...")
        
        # Use UPSERT logic
        query = """
            INSERT INTO assets (symbol, name, type) 
            VALUES %s 
            ON CONFLICT (symbol) 
            DO UPDATE SET name = EXCLUDED.name, type = EXCLUDED.type
        """
        execute_values(remote_cur, query, assets)
        
        remote_conn.commit()
        print("Sync complete! All asset names and descriptions are now on Supabase.")
        
    except Exception as e:
        print(f"Sync failed: {e}")
    finally:
        if 'local_conn' in locals(): local_conn.close()
        if 'remote_conn' in locals(): remote_conn.close()

if __name__ == "__main__":
    if not REMOTE_DB["password"]:
        print("Error: REMOTE_DB_PASSWORD not set. Please set it in your environment.")
    else:
        sync()
