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

def load_all_csvs():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to database.")
    except Exception as e:
        print(f"FAILED to connect to database: {e}")
        return

    # Find all CSV files in subfolders of data/
    csv_files = list(BASE_DATA_DIR.glob("**/*.csv"))
    print(f"Found {len(csv_files)} CSV files to process.")

    loaded_count = 0
    skipped_count = 0

    for csv_path in csv_files:
        asset_type = csv_path.parent.name
        ticker = csv_path.stem.upper()
        
        print(f"Processing {ticker} ({asset_type})...", end=" ", flush=True)
        
        try:
            df = pd.read_csv(csv_path)
            
            # Simple Column Mismatch Check
            required_cols = {'date', 'close', 'adj_close', 'volume'}
            if not required_cols.issubset(set(df.columns)):
                print(f"\nERROR: Column mismatch in {csv_path}. Found: {df.columns.tolist()}")
                print("STOPPING SCAN TO PREVENT CORRUPTION.")
                sys.exit(1)

            cur = conn.cursor()

            # 1. Ensure asset exists
            cur.execute(
                "INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) ON CONFLICT (symbol) DO UPDATE SET type=EXCLUDED.type RETURNING id",
                (ticker, ticker, asset_type)
            )
            asset_id = cur.fetchone()[0]

            # 2. Upsert Prices
            values = []
            for _, row in df.iterrows():
                values.append((
                    asset_id,
                    str(row['date'])[:10],
                    float(row['close']),
                    float(row['adj_close']),
                    int(row['volume']) if not pd.isna(row['volume']) else 0
                ))

            upsert_query = """
                INSERT INTO prices (asset_id, date, close, adj_close, volume)
                VALUES %s
                ON CONFLICT (asset_id, date) DO UPDATE SET 
                    close = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume = EXCLUDED.volume
            """
            execute_values(cur, upsert_query, values)
            conn.commit()
            
            print("DONE.")
            loaded_count += 1

        except Exception as e:
            print(f"\nCRITICAL ERROR processing {ticker}: {e}")
            print("STOPPING SCAN AND FIXING...")
            if conn: conn.rollback()
            # If it's a DB error (like col ID mismatch), we stop.
            sys.exit(1)

    print(f"\nSummary: Loaded {loaded_count}, Skipped {skipped_count}")
    if conn: conn.close()

if __name__ == "__main__":
    load_all_csvs()
