import os
import yfinance as yf
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "stocksim"),
    "user": os.getenv("DB_USER", "stocksim"),
    "password": os.getenv("DB_PASSWORD", "stocksim"),
    "host": os.getenv("DB_HOST", "localhost")
}

def update_asset_names():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get all stocks currently in DB
        cur.execute("SELECT id, symbol FROM assets WHERE type = 'stocks'")
        assets = cur.fetchall()

        print(f"Found {len(assets)} stocks to update.")

        for asset_id, symbol in assets:
            try:
                print(f"Updating {symbol}...")
                ticker = yf.Ticker(symbol)
                name = ticker.info.get('longName') or ticker.info.get('shortName')
                
                if name:
                    cur.execute("UPDATE assets SET name = %s WHERE id = %s", (name, asset_id))
                    print(f"  -> {name}")
                else:
                    print(f"  -> No name found")
            except Exception as e:
                print(f"  -> Error: {e}")

        conn.commit()
        print("Update complete!")

    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    update_asset_names()
