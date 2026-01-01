import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

DB = dict(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost")
)


def connect():
    """Establishes a connection to the database."""
    try:
        return psycopg2.connect(**DB)
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def get_asset_id(symbol: str):
    """
    Retrieves the asset ID for a given symbol.
    """
    conn = connect()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_price(symbol: str, date: str):
    """
    Get the adjusted close price for a symbol on a specific date.
    If the date is missing (e.g., weekend/holiday), looks for the next available trading day
    within a 7-day window.
    """
    asset_id = get_asset_id(symbol)
    if not asset_id:
        return None

    conn = connect()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        # Try exact match first
        query = "SELECT adj_close FROM prices WHERE asset_id = %s AND date = %s"
        cur.execute(query, (asset_id, date))
        row = cur.fetchone()

        if row:
            return float(row[0])

        # Fallback: Find closest FUTURE date (up to 7 days)
        # We want the price at which you *could* trade if you tried on 'date'
        query_fallback = """
            SELECT adj_close, date 
            FROM prices 
            WHERE asset_id = %s AND date > %s 
            ORDER BY date ASC 
            LIMIT 1
        """
        cur.execute(query_fallback, (asset_id, date))
        row = cur.fetchone()

        if row:
            # Check if it's within a reasonable window (e.g., 7 days)
            found_date = row[1]
            input_date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            if (found_date - input_date_obj).days <= 7:
                return float(row[0])

        return None

    except Exception as e:
        print(f"Error fetching price for {symbol} on {date}: {e}")
        return None
    finally:
        conn.close()

# Alias for backward compatibility if needed, but get_price is smarter
get_adj_close = get_price