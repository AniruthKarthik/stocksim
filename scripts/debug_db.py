import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db_conn import get_db_connection

def test_connection():
    print("Testing DB Connection...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                res = cur.fetchone()
                print(f"Success! Result: {res}")
                cur.execute("SELECT version();")
                ver = cur.fetchone()
                print(f"DB Version: {ver[0]}")
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()
