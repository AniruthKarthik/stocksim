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

def get_all_assets(as_of_date: str = None):
    """
    Returns a list of all tradable assets, excluding mutual funds.
    If as_of_date is provided, only returns assets that have a price within 
    the 30 days prior to or on that date (actively trading).
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            if as_of_date:
                # Optimized: Return assets that have ANY price history on or before the simulation date.
                # Removed the 30-day "active" window to support future simulation dates using latest available data.
                query = """
                    SELECT symbol, name, type 
                    FROM assets a
                    WHERE a.type != 'mutualfunds' 
                      AND EXISTS (
                          SELECT 1 FROM prices p 
                          WHERE p.asset_id = a.id 
                          AND p.date <= %s 
                      )
                    ORDER BY a.type, a.symbol
                """
                cur.execute(query, (as_of_date,))
            else:
                query = "SELECT symbol, name, type FROM assets WHERE type != 'mutualfunds' ORDER BY type, symbol"
                cur.execute(query)
                
            rows = cur.fetchall()
            return [{"symbol": r[0], "name": r[1], "type": r[2]} for r in rows]
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
