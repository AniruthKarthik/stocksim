
import psycopg2
import os
import yfinance as yf
import time

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost")
}

def update_names():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get assets where name looks like symbol
        cur.execute("SELECT id, symbol FROM assets WHERE name = symbol OR name = symbol::text")
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} assets with missing names.")
        
        updated_count = 0
        
        for asset_id, symbol in rows:
            try:
                # Add delay to avoid rate limiting
                time.sleep(0.2) 
                
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Try to find a good name
                long_name = info.get('longName')
                short_name = info.get('shortName')
                
                new_name = long_name or short_name
                
                if new_name:
                    # Clean up common suffixes if desired, or keep them for "expanded form"
                    # The user wants "expanded form", so full name is good.
                    
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
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    update_names()
