import os
import sys
import psycopg2

# Add project root to path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db_conn import get_db_connection

def migrate_crypto():
    print("--- Migrating Crypto Assets ---")
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Find crypto assets
            cur.execute("SELECT id, symbol FROM assets WHERE type = 'crypto'")
            rows = cur.fetchall()
            
            for asset_id, symbol in rows:
                if not symbol.endswith('-USD'):
                    new_symbol = f"{symbol}-USD"
                    print(f"Migrating {symbol} -> {new_symbol}")
                    try:
                        cur.execute("UPDATE assets SET symbol = %s WHERE id = %s", (new_symbol, asset_id))
                        # Also update transactions
                        cur.execute("UPDATE transactions SET symbol = %s WHERE asset_id = %s", (new_symbol, asset_id))
                    except Exception as e:
                        print(f"Failed to migrate {symbol}: {e}")
                        conn.rollback()
                        continue
            
            conn.commit()
            print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_crypto()