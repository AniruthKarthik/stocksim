import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost")
)


def connect():
    return psycopg2.connect(**DB)


def get_asset_id(symbol: str):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
    row = cur.fetchone()

    conn.close()

    return row[0] if row else None


def get_adj_close(symbol: str, date: str):
    asset_id = get_asset_id(symbol)
    if not asset_id:
        return None

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT adj_close
        FROM prices
        WHERE asset_id = %s AND date = %s
        """, (asset_id, date)
    )

    row = cur.fetchone()
    conn.close()

    return float(row[0]) if row else None

