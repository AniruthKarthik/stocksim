from functools import lru_cache
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


@lru_cache(maxsize=4096)
def get_price(symbol: str, date: str):
    """
    Get the adjusted close price for a symbol on a specific date.
    Finds the latest available price on or before 'date'.
    Cached to make portfolio valuation near-instant.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
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

@lru_cache(maxsize=1)
def get_asset_start_dates():
    """
    Returns a dictionary {asset_id: start_date_string} for all assets.
    This query is heavy (GROUP BY) so we cache it aggressively.
    Since history doesn't change often (only on nightly updates), this is safe.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # Efficiently get the first available date for every asset
            cur.execute("SELECT asset_id, MIN(date) FROM prices GROUP BY asset_id")
            return {row[0]: str(row[1]) for row in cur.fetchall()}
    except Exception as e:
        print(f"Error fetching asset start dates: {e}")
        return {}

@lru_cache(maxsize=1)
def get_assets_metadata():
    """
    Returns list of all assets without filtering. Cached.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, symbol, name, type, currency FROM assets ORDER BY symbol")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching assets metadata: {e}")
        return []

def get_all_assets(date: str = None):
    """
    Returns list of all supported assets.
    If date is provided, filters for assets that have price data on or before that date
    using cached metadata to avoid DB hits.
    """
    all_assets = get_assets_metadata()
    
    if not date:
        return all_assets

    # Filter in memory using cached start dates
    start_dates = get_asset_start_dates()
    
    # Check if asset exists and started on or before the simulation date
    filtered = []
    for asset in all_assets:
        aid = asset.get('id')
        start_date = start_dates.get(aid)
        if start_date and start_date <= date:
            filtered.append(asset)
            
    return filtered

def get_asset_details(symbol: str):
    """
    Returns full details for an asset (name, type, etc.)
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT symbol, name, type, currency FROM assets WHERE symbol = %s", (symbol.upper(),))
            row = cur.fetchone()
            if row:
                return {"symbol": row[0], "name": row[1], "type": row[2], "currency": row[3]}
            return None
    except Exception as e:
        print(f"Error fetching asset details: {e}")
        return None

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