from .db_conn import get_db_connection

def get_asset_id(symbol: str):
    """
    Retrieves the asset ID for a given symbol.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM assets WHERE symbol = %s", (symbol,))
            row = cur.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"Error fetching asset ID: {e}")
        return None


def get_price(symbol: str, date: str):
    """
    Get the adjusted close price for a symbol on a specific date.
    Optimized to use a single query and connection.
    Finds the latest available price on or before 'date' (Last Known Close).
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # optimized single query with join
            query = """
                SELECT p.adj_close 
                FROM prices p
                JOIN assets a ON p.asset_id = a.id
                WHERE a.symbol = %s AND p.date <= %s
                ORDER BY p.date DESC
                LIMIT 1
            """
            cur.execute(query, (symbol, date))
            row = cur.fetchone()
            if row:
                return float(row[0])
            return None
    except Exception as e:
        print(f"Error fetching price for {symbol} on {date}: {e}")
        return None

from functools import lru_cache

@lru_cache(maxsize=128)
def get_all_assets(date: str = None):
    """
    Returns list of all supported assets.
    If date is provided, filters for assets that have price data on or before that date.
    Cached to improve performance.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            if date:
                # Optimized query: Find assets that have at least one price entry <= date
                # Using EXISTS is often faster than DISTINCT JOIN on large tables
                query = """
                    SELECT symbol, name, type, currency 
                    FROM assets a
                    WHERE EXISTS (
                        SELECT 1 FROM prices p 
                        WHERE p.asset_id = a.id AND p.date <= %s
                    )
                    ORDER BY symbol
                """
                cur.execute(query, (date,))
            else:
                cur.execute("SELECT symbol, name, type, currency FROM assets ORDER BY symbol")
                
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching assets: {e}")
        return []

def get_price_history(symbol: str, end_date: str):
    """
    Returns daily price history for a symbol up to end_date.
    Optimized to use a single query with JOIN.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT p.date, p.adj_close 
                FROM prices p
                JOIN assets a ON p.asset_id = a.id
                WHERE a.symbol = %s AND p.date <= %s 
                ORDER BY p.date ASC
            """
            cur.execute(query, (symbol, end_date))
            rows = cur.fetchall()
            # Return list of { date: "YYYY-MM-DD", price: 123.45 }
            return [{"date": r[0].isoformat(), "price": float(r[1])} for r in rows]
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

# Alias for backward compatibility if needed, but get_price is smarter
get_adj_close = get_price

# Backward compatibility alias for connect if other modules import it directly
# but they should be refactored. We'll leave a dummy or remove it.
# We will remove it to force errors if we missed something.
