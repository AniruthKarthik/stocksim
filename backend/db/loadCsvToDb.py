import os
import psycopg2
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# load environment variables
load_dotenv()

DB = dict(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost")
)

# Fix: Robust path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def connect():
    return psycopg2.connect(**DB)


def get_or_create_asset(symbol, name, asset_type, currency="USD"):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO assets (symbol, name, type, currency)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (symbol)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING id;
    """, (symbol, name, asset_type, currency))

    asset_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return asset_id


def load_prices(asset_id, csv_path):
    df = pd.read_csv(csv_path)

    # validate required fields
    required = ["date", "close", "adj_close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"  ⚠️ Skipping {csv_path} — missing columns: {missing}")
        return

    conn = connect()
    cur = conn.cursor()

    for _, r in df.iterrows():
        cur.execute("""
            INSERT INTO prices (assetid, date, close, adjclose, vol)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (assetid, date) DO NOTHING;
        """, (
            asset_id,
            r["date"],
            float(r["close"]),
            float(r["adj_close"]),
            int(r["volume"]) if pd.notna(r["volume"]) else 0
        ))

    conn.commit()
    conn.close()


def load_all():
    if not BASE_DIR.exists():
        print("❌ data/ folder not found")
        return

    for folder in BASE_DIR.iterdir():
        if not folder.is_dir():
            continue

        asset_type = folder.name.lower()
        print(f"\n--- Loading {asset_type} ---")

        for csv_file in folder.glob("*.csv"):
            symbol = csv_file.stem.upper()
            name = csv_file.stem.replace("_", " ").title()

            print(f"→ {symbol}")

            asset_id = get_or_create_asset(symbol, name, asset_type)
            load_prices(asset_id, csv_file)

    print("\n✓ All data loaded successfully")


if __name__ == "__main__":
    load_all()
