import os
import sys
import psycopg2

# Add project root to path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db_conn import get_db_connection

def cleanup():
    print("--- Database Cleanup ---")
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Clean up users/portfolios/sessions
            print("Cleaning user data...")
            cur.execute("TRUNCATE TABLE users, portfolios, game_sessions, transactions CASCADE")
            
            # Reset sequences
            print("Resetting sequences...")
            cur.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE portfolios_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE game_sessions_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE transactions_id_seq RESTART WITH 1")
            
            conn.commit()
            print("Cleanup successful.")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    cleanup()