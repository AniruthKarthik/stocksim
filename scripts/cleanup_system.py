import os
import glob
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "stocksim"),
    "user": os.getenv("DB_USER", "stocksim"),
    "password": os.getenv("DB_PASSWORD", "stocksim"),
    "host": os.getenv("DB_HOST", "localhost")
}

BASE_DATA_DIR = Path("data")

def get_allowed_tickers():
    """Reads all ticker files and returns a set of allowed symbols."""
    allowed = set()
    ticker_files = list(BASE_DATA_DIR.glob("*_tickers.txt"))
    
    print(f"Reading valid tickers from {len(ticker_files)} files...")
    
    for file_path in ticker_files:
        with open(file_path, 'r') as f:
            for line in f:
                clean = line.split('#')[0].strip()
                if clean:
                    # Normalize: The system seems to use upper case for symbols
                    allowed.add(clean.upper())
    
    return allowed

def clean_csv_files(allowed_tickers):
    """Deletes CSV files that are not in the allowed list."""
    print("\n--- Cleaning CSV Files ---")
    deleted_count = 0
    
    # We look at all subdirectories in data/
    for csv_file in BASE_DATA_DIR.glob("**/*.csv"):
        # The file stem is usually the symbol (e.g. BTC-USD.csv -> BTC-USD)
        # However, previous scripts might have saved 'bitcoin.csv'.
        # We delete if the stem (upper) is not in allowed tickers.
        
        file_symbol = csv_file.stem.upper()
        
        # Special check: Yahoo tickers often use hyphens, but filenames might be different?
        # In our current setup, refresh_stocks saves as {ticker}.csv.
        # So we strictly check if file_symbol is in allowed_tickers.
        
        if file_symbol not in allowed_tickers:
            print(f"Removing orphan file: {csv_file}")
            try:
                os.remove(csv_file)
                deleted_count += 1
            except OSError as e:
                print(f"Error removing {csv_file}: {e}")
                
    print(f"Deleted {deleted_count} orphan CSV files.")

def clean_database(allowed_tickers):
    """Deletes assets from DB that are not in the allowed list."""
    print("\n--- Cleaning Database ---")
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get all existing assets
        cur.execute("SELECT id, symbol FROM assets")
        rows = cur.fetchall()
        
        to_delete_ids = []
        to_delete_symbols = []
        
        for asset_id, symbol in rows:
            # Check if symbol is allowed
            # Also check for symbols with =F specifically requested to be removed
            if symbol not in allowed_tickers:
                to_delete_ids.append(asset_id)
                to_delete_symbols.append(symbol)
            elif "=F" in symbol:
                 # Double check in case an =F sneaked into allowed_tickers (unlikely)
                 to_delete_ids.append(asset_id)
                 to_delete_symbols.append(symbol)

        if not to_delete_ids:
            print("Database is already clean.")
            return

        print(f"Found {len(to_delete_ids)} assets to remove from DB:")
        print(f"{to_delete_symbols[:10]} ...")

        # 1. Delete transactions referencing these assets (Fix for FK constraint)
        print("  Removing related transactions...")
        cur.execute("DELETE FROM transactions WHERE asset_id = ANY(%s)", (to_delete_ids,))

        # 2. Delete prices (Foreign Key constraint usually cascades, but good to be explicit)
        print("  Removing related price history...")
        cur.execute("DELETE FROM prices WHERE asset_id = ANY(%s)", (to_delete_ids,))
        
        # 3. Delete the assets themselves
        print("  Removing assets...")
        cur.execute("DELETE FROM assets WHERE id = ANY(%s)", (to_delete_ids,))
        
        conn.commit()
        print(f"Successfully removed {len(to_delete_ids)} assets, their prices, and related transactions.")
        
    except Exception as e:
        print(f"Database error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    allowed = get_allowed_tickers()
    if not allowed:
        print("No tickers found! Aborting to prevent deleting everything.")
    else:
        clean_csv_files(allowed)
        clean_database(allowed)
