import os
import shutil
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

def migrate_crypto():
    print("--- Starting Crypto Migration (Removing -USD suffix) ---")
    
    # 1. Update crypto_tickers.txt
    ticker_file = Path("data/crypto_tickers.txt")
    if ticker_file.exists():
        print("Updating crypto_tickers.txt...")
        with open(ticker_file, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            clean = line.strip().upper()
            if clean.endswith("-USD"):
                clean = clean.replace("-USD", "")
            new_lines.append(clean + "\n")
            
        with open(ticker_file, 'w') as f:
            f.writelines(new_lines)
        print("✓ Ticker file updated.")
    
    # 2. Rename CSV files
    crypto_dir = Path("data/crypto")
    if crypto_dir.exists():
        print("Renaming CSV files...")
        count = 0
        for csv_file in crypto_dir.glob("*-USD.csv"):
            new_name = csv_file.name.replace("-USD.csv", ".csv")
            new_path = crypto_dir / new_name
            try:
                csv_file.rename(new_path)
                count += 1
            except Exception as e:
                print(f"Error renaming {csv_file.name}: {e}")
        print(f"✓ Renamed {count} CSV files.")

    # 3. Update Database
    print("Updating Database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check usage in transactions first? 
        # If we update the asset symbol, the ID remains the same, so transactions (FK to ID) are safe!
        # We just need to update the 'symbol' column in 'assets'.
        # AND 'symbol' column in 'transactions' table (it copies the symbol).
        
        # 1. Update assets table
        cur.execute("""
            UPDATE assets 
            SET symbol = REPLACE(symbol, '-USD', '') 
            WHERE type = 'crypto' AND symbol LIKE '%-USD'
        """)
        updated_assets = cur.rowcount
        
        # 2. Update transactions table (if it stores symbol text, which it does)
        cur.execute("""
            UPDATE transactions
            SET symbol = REPLACE(symbol, '-USD', '')
            WHERE symbol LIKE '%-USD' 
              AND asset_id IN (SELECT id FROM assets WHERE type = 'crypto')
        """)
        updated_txns = cur.rowcount
        
        conn.commit()
        conn.close()
        print(f"✓ Database updated: {updated_assets} assets, {updated_txns} transactions modified.")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    migrate_crypto()
