import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db_conn import get_db_connection

load_dotenv()

BASE_DATA_DIR = Path("data")

def load_csvs_to_db():
    print("--- Loading Local CSVs into Database ---")
    
    try:
        with get_db_connection() as conn:
            # Gather all CSVs
            csv_files = list(BASE_DATA_DIR.glob("**/*.csv"))
            print(f"Found {len(csv_files)} CSV files in {BASE_DATA_DIR}")

            loaded_count = 0
            skipped_count = 0
            
            for csv_path in csv_files:
                try:
                    # Derive info from path
                    asset_type = csv_path.parent.name # e.g. "stocks"
                    ticker = csv_path.stem.upper()    # e.g. "AAPL"

                    if asset_type == "data":
                        continue

                    print(f"Processing {ticker} ({asset_type})...", end=" ", flush=True)

                    df = pd.read_csv(csv_path)
                    
                    required = {'date', 'close', 'adj_close', 'volume'}
                    if not required.issubset(df.columns):
                        print(f"SKIPPED (Missing columns: {required - set(df.columns)})")
                        skipped_count += 1
                        continue

                    cur = conn.cursor()

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
                        cur.execute("SELECT id FROM assets WHERE symbol = %s", (ticker,))
                        asset_id = cur.fetchone()[0]

                    values = []
                    for _, row in df.iterrows():
                        d_str = str(row['date'])[:10]
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
                    conn.rollback()
                    print(f"ERROR processing {ticker}: {e}")
                    skipped_count += 1

            print(f"\nSummary: Processed {loaded_count} files. Skipped/Error {skipped_count}.")
    except Exception as e:
        print(f"Fatal error during CSV load: {e}")

if __name__ == "__main__":
    load_csvs_to_db()