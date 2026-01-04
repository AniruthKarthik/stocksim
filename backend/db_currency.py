import yfinance as yf
from datetime import datetime, timedelta
from .db_prices import connect

# Mapping currency code to Yahoo Finance ticker
# We want Rate = (Foreign / USD).
# If ticker is "EURUSD=X", it gives USD per 1 EUR. So 1 EUR = 1.05 USD. We want EUR per USD. So 1/1.05.
# If ticker is "USDJPY=X", it gives JPY per 1 USD. So 1 USD = 150 JPY. This is direct.
# Most are "USD{XXX}=X".
TICKERS = {
    'EUR': 'EUR=X', # 1 EUR in USD (approx 1.05). We want USD->EUR. So 1/Price.
    'GBP': 'GBP=X', # 1 GBP in USD. We want USD->GBP. So 1/Price.
    'JPY': 'JPY=X', # 1 USD in JPY. (Normally USDJPY=X)
    'CAD': 'CAD=X', # 1 USD in CAD. (Normally USDCAD=X)
    'AUD': 'AUDUSD=X', # 1 AUD in USD. Wait. YF convention varies.
    'INR': 'INR=X'  # 1 USD in INR?
}

# Let's standardize.
# We will use "USD{CODE}=X" where possible.
# USD/EUR -> "USDEUR=X" doesn't usually exist. "EUR=X" is EUR/USD.
# Let's verify standard pairs.
# EURUSD=X (1 EUR = $x)
# GBPUSD=X (1 GBP = $x)
# USDJPY=X (1 USD = ¥x)
# USDCAD=X (1 USD = C$x)
# AUDUSD=X (1 AUD = $x)
# USDINR=X (1 USD = ₹x)

def fetch_live_rates():
    """
    Fetches rates from Yahoo Finance.
    Returns dictionary: { 'EUR': 0.95, 'JPY': 150, ... } (Amount of Currency per 1 USD)
    """
    rates = {'USD': 1.0}
    
    # List of tickers to fetch
    # We need to know how to interpret them.
    # Inverse pairs (Target is Base): EUR=X, GBP=X, AUDUSD=X (Quotes are in USD)
    # Direct pairs (USD is Base): JPY=X, CAD=X, INR=X (Quotes are in Target)
    
    # Note: yfinance tickers:
    # 'EUR=X' -> Quote is USD per EUR. (e.g. 1.05). Rate (EUR per USD) = 1/1.05
    # 'JPY=X' -> Quote is JPY per USD. (e.g. 154). Rate = 154.
    
    to_fetch = {
        'EUR': 'EUR=X', # USD per EUR
        'GBP': 'GBP=X', # USD per GBP
        'AUD': 'AUDUSD=X', # USD per AUD
        'JPY': 'JPY=X', # JPY per USD
        'CAD': 'CAD=X', # CAD per USD
        'INR': 'INR=X'  # INR per USD
    }
    
    inverse_quotes = ['EUR', 'GBP', 'AUD'] # Result is USD cost. We want units per USD.
    
    tickers_str = " ".join(to_fetch.values())
    try:
        data = yf.download(tickers_str, period="1d", progress=False)['Close']
        # data might be DataFrame with MultiIndex or Single.
        
        # Safe access to latest value
        def get_val(ticker):
            try:
                if len(data.shape) > 1: # DataFrame
                    # If multiple tickers, columns are (Price, Ticker)
                    # or just Ticker if simple.
                    # yfinance structure varies. 'Close' -> columns are tickers.
                    series = data[ticker]
                    val = series.iloc[-1]
                else:
                    val = data.iloc[-1]
                return float(val)
            except:
                return None

        for code, ticker in to_fetch.items():
            val = get_val(ticker)
            if val and val > 0:
                if code in inverse_quotes:
                    rates[code] = 1.0 / val
                else:
                    rates[code] = val
                    
    except Exception as e:
        print(f"Error fetching rates: {e}")
        # Return partial or empty (will fallback to DB)
        
    return rates

def update_rates_if_needed():
    """
    Checks if rates are stale (older than 24h). If so, updates them.
    """
    conn = connect()
    if not conn: return
    
    try:
        cur = conn.cursor()
        
        # Check oldest update time
        cur.execute("SELECT MIN(last_updated) FROM exchange_rates WHERE currency_code != 'USD'")
        row = cur.fetchone()
        
        needs_update = True
        if row and row[0]:
            last_update = row[0]
            if (datetime.now() - last_update) < timedelta(hours=24):
                needs_update = False
                
        if needs_update:
            print("Updating currency rates...")
            rates = fetch_live_rates()
            for code, rate in rates.items():
                if code == 'USD': continue
                cur.execute("""
                    INSERT INTO exchange_rates (currency_code, rate, last_updated)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (currency_code) 
                    DO UPDATE SET rate = %s, last_updated = NOW()
                """, (code, rate, rate))
            conn.commit()
            print("Rates updated.")
            
    except Exception as e:
        print(f"Error in rate update: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_all_rates():
    """
    Returns list of { code, name, symbol, rate }
    """
    # Ensure fresh
    update_rates_if_needed()
    
    conn = connect()
    if not conn: return []
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.code, c.name, c.symbol, COALESCE(e.rate, 0)
            FROM currencies c
            LEFT JOIN exchange_rates e ON c.code = e.currency_code
            ORDER BY c.code
        """)
        rows = cur.fetchall()
        return [
            {"code": r[0], "name": r[1], "symbol": r[2], "rate": float(r[3])} 
            for r in rows
        ]
    finally:
        conn.close()

def get_rate(code: str):
    """
    Returns the rate for a specific currency code (units per 1 USD).
    """
    if code == 'USD': return 1.0
    
    update_rates_if_needed()
    conn = connect()
    if not conn: return 1.0
    try:
        cur = conn.cursor()
        cur.execute("SELECT rate FROM exchange_rates WHERE currency_code = %s", (code,))
        row = cur.fetchone()
        return float(row[0]) if row else 1.0
    finally:
        conn.close()
