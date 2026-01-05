import os
import sys
import yfinance as yf
import time

# Add project root to path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db_conn import get_db_connection

def update_names():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, symbol FROM assets WHERE name = symbol OR name = symbol::text")
            rows = cur.fetchall()
            
            print(f"Found {len(rows)} assets with missing names.")
            updated_count = 0
            
            for asset_id, symbol in rows:
                try:
                    time.sleep(0.2) 
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    long_name = info.get('longName')
                    short_name = info.get('shortName')
                    new_name = long_name or short_name
                    
                    if new_name:
                        cur.execute("UPDATE assets SET name = %s WHERE id = %s", (new_name, asset_id))
                        conn.commit()
                        print(f"Updated {symbol} -> {new_name}")
                        updated_count += 1
                    else:
                        print(f"Could not find name for {symbol}")
                except Exception as e:
                    print(f"Failed to fetch/update {symbol}: {e}")
            print(f"Finished. Updated {updated_count} assets.")
    except Exception as e:
        print(f"Script error: {e}")

if __name__ == "__main__":
    update_names()