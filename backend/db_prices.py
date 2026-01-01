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

        # Fallback: Find most recent PAST date (Last Known Close)
        # We want the latest price available on or before 'date'
        query_fallback = """
            SELECT adj_close, date 
            FROM prices 
            WHERE asset_id = %s AND date < %s 
            ORDER BY date DESC 
            LIMIT 1
        """
        cur.execute(query_fallback, (asset_id, date))
        row = cur.fetchone()

        if row:
            # We return the last known price regardless of how old it is
            # This ensures we always have a value for valuation purposes
            return float(row[0])

        return None

    except Exception as e:
        print(f"Error fetching price for {symbol} on {date}: {e}")
        return None
    finally:
        conn.close()

def get_all_assets(as_of_date: str = None):
    """
    Returns a list of all tradable assets, excluding mutual funds.
    If as_of_date is provided, only returns assets that have a price within 
    the 30 days prior to or on that date (actively trading).
    """
    conn = connect()
    if not conn: return []
    try:
        cur = conn.cursor()
        
        if as_of_date:
            # Only include assets that have data in the 30 days leading up to as_of_date
            query = """
                SELECT DISTINCT a.symbol, a.name, a.type 
                FROM assets a
                JOIN prices p ON a.id = p.asset_id
                WHERE a.type != 'mutualfunds' 
                  AND p.date <= %s 
                  AND p.date >= (%s::date - interval '30 days')
                ORDER BY a.type, a.symbol
            """
            cur.execute(query, (as_of_date, as_of_date))
        else:
            query = "SELECT symbol, name, type FROM assets WHERE type != 'mutualfunds' ORDER BY type, symbol"
            cur.execute(query)
            
        rows = cur.fetchall()
        return [{"symbol": r[0], "name": r[1], "type": r[2]} for r in rows]
    except Exception as e:
        print(f"Error fetching assets: {e}")
        return []
    finally:
        conn.close()

def get_price_history(symbol: str, end_date: str):
    """
    Returns daily price history for a symbol up to end_date.
    """
    asset_id = get_asset_id(symbol)
    if not asset_id: return []

    conn = connect()
    if not conn: return []
    try:
        cur = conn.cursor()
        query = """
            SELECT date, adj_close 
            FROM prices 
            WHERE asset_id = %s AND date <= %s 
            ORDER BY date ASC
        """
        cur.execute(query, (asset_id, end_date))
        rows = cur.fetchall()
        # Return list of { date: "YYYY-MM-DD", price: 123.45 }
        return [{"date": r[0].isoformat(), "price": float(r[1])} for r in rows]
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []
    finally:
        conn.close()

# Alias for backward compatibility if needed, but get_price is smarter
get_adj_close = get_price
