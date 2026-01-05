import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "stocksim"),
    "user": os.getenv("DB_USER", "stocksim"),
    "password": os.getenv("DB_PASSWORD", "stocksim"),
    "host": os.getenv("DB_HOST", "localhost")
}

BASE_DATA_DIR = Path("data")

def connect():
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return psycopg2.connect(db_url, sslmode='require')
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def load_csvs_to_db():
    print("--- Loading Local CSVs into Database ---")
    
    conn = connect()
    if not conn: return

    # Gather all CSVs
    csv_files = list(BASE_DATA_DIR.glob("**/*.csv"))
    print(f"Found {len(csv_files)} CSV files in {BASE_DATA_DIR}")

    loaded_count = 0
    skipped_count = 0
    
    for csv_path in csv_files:
        try:
            # Derive info from path
            # Structure: data/stocks/AAPL.csv
            asset_type = csv_path.parent.name # e.g. "stocks"
            ticker = csv_path.stem.upper()    # e.g. "AAPL"

            # Skip if asset_type is just "data" (misplaced file)
            if asset_type == "data":
                continue

            print(f"Processing {ticker} ({asset_type})...", end=" ", flush=True)

            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Basic validation
            required = {'date', 'close', 'adj_close', 'volume'}
            if not required.issubset(df.columns):
                print(f"SKIPPED (Missing columns: {required - set(df.columns)})")
                skipped_count += 1
                continue

            cur = conn.cursor()

            # 1. Ensure Asset Exists
            cur.execute(
                """INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) 
                   ON CONFLICT (symbol) DO NOTHING 
                   RETURNING id""",
                (ticker, ticker, asset_type)
            )
            res = cur.fetchone()
            
            if res:
                asset_id = res[0]
            else:
                # Already exists, fetch ID
                cur.execute("SELECT id FROM assets WHERE symbol = %s", (ticker,))
                asset_id = cur.fetchone()[0]

            # 2. Bulk Insert Prices (Ignore Duplicates)
            # Prepare data
            values = []
            for _, row in df.iterrows():
                # Safe date parsing
                d_str = str(row['date'])[:10]
                
                # Handle potential NaN in volume
                vol = 0
                if pd.notna(row['volume']):
                    try:
                        vol = int(row['volume'])
                    except:
                        vol = 0
                        
                values.append(( 
                    asset_id,
                    d_str,
                    float(row['close']),
                    float(row['adj_close']),
                    vol
                ))

            if not values:
                print("EMPTY FILE.")
                continue

            # Efficient Upsert (DO NOTHING on conflict)
            query = """
                INSERT INTO prices (asset_id, date, close, adj_close, volume)
                VALUES %s
                ON CONFLICT (asset_id, date) DO NOTHING
            """
            execute_values(cur, query, values)
            conn.commit()
            
            print("✓")
            loaded_count += 1

        except Exception as e:
            if conn: conn.rollback()
            print(f"ERROR: {e}")
            skipped_count += 1

    conn.close()
    print(f"\nSummary: Processed {loaded_count} files. Skipped/Error {skipped_count}.")

if __name__ == "__main__":
    load_csvs_to_db()
