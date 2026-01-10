import yfinance as yf
from datetime import datetime, timedelta
from .db_conn import get_db_connection

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
    
    # Standardizing to {CODE}=X which usually gives units per 1 USD for most currencies
    # or is the most reliable ticker.
    to_fetch = {
        'EUR': 'EUR=X', 
        'GBP': 'GBP=X', 
        'AUD': 'AUD=X', 
        'JPY': 'JPY=X', 
        'CAD': 'CAD=X', 
        'INR': 'INR=X'  
    }
    
    tickers_str = " ".join(to_fetch.values())
    try:
        # Fetching 5 days to ensure we get data even if market is closed today
        data = yf.download(tickers_str, period="5d", progress=False)['Close']
        
        # Safe access to latest non-NaN value
        def get_val(ticker):
            try:
                if isinstance(data, pd.DataFrame):
                    # Get the series for the ticker and drop NaNs
                    series = data[ticker].dropna()
                    if not series.empty:
                        return float(series.iloc[-1])
                else:
                    # If only one ticker was requested, data might be a Series
                    val = data.iloc[-1]
                    return float(val) if pd.notna(val) else None
                return None
            except:
                return None

        for code, ticker in to_fetch.items():
            val = get_val(ticker)
            if val and val > 0:
                # All these tickers now represent Units per USD
                rates[code] = val
                    
    except Exception as e:
        print(f"Error fetching rates: {e}")
        
    return rates

def update_rates_if_needed():
    """
    Checks if rates are stale (older than 24h). If so, updates them.
    """
    try:
        with get_db_connection() as conn:
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

def get_all_rates():
    """
    Returns list of { code, name, symbol, rate }
    Ensures fresh data and fallbacks.
    """
    try:
        update_rates_if_needed()
    except Exception as e:
        print(f"WARNING: Rate update failed, using existing/fallback: {e}")
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.code, c.name, c.symbol, COALESCE(e.rate, 0)
                FROM currencies c
                LEFT JOIN exchange_rates e ON c.code = e.currency_code
                ORDER BY c.code
            """)
            rows = cur.fetchall()
            res = []
            for r in rows:
                code, name, symbol, rate = r
                # If rate is 0 or missing, use hardcoded fallback
                if not rate or float(rate) <= 0:
                    rate = FALLBACK_RATES.get(code, 1.0)
                res.append({
                    "code": code, 
                    "name": name, 
                    "symbol": symbol, 
                    "rate": float(rate)
                })
            
            # Ensure USD is always exactly 1.0 regardless of DB state
            for r in res:
                if r['code'] == 'USD':
                    r['rate'] = 1.0
                    
            return res
    except Exception as e:
        print(f"ERROR in get_all_rates: {e}")
        # Final fallback for the whole list
        return [
            {"code": code, "name": name, "symbol": symbol, "rate": float(FALLBACK_RATES.get(code, 1.0))}
            for code, name, symbol in [
                ('USD', 'United States Dollar', '$'),
                ('INR', 'Indian Rupee', '₹'),
                ('EUR', 'Euro', '€'),
                ('GBP', 'British Pound', '£'),
                ('JPY', 'Japanese Yen', '¥'),
                ('CAD', 'Canadian Dollar', 'C$'),
                ('AUD', 'Australian Dollar', 'A$')
            ]
        ]

# Hardcoded fallback rates (Amount per 1 USD)
# Used if Yahoo Finance is unreachable or DB is empty.
FALLBACK_RATES = {
    'USD': 1.0,
    'INR': 83.5,
    'EUR': 0.92,
    'GBP': 0.79,
    'JPY': 155.0,
    'CAD': 1.37,
    'AUD': 1.51
}

def get_rate(code: str):
    """
    Returns the rate for a specific currency code (units per 1 USD).
    """
    if not code or code == 'USD': return 1.0
    
    update_rates_if_needed()
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT rate FROM exchange_rates WHERE currency_code = %s", (code,))
            row = cur.fetchone()
            if row and float(row[0]) > 0:
                return float(row[0])
    except Exception as e:
        print(f"DEBUG: Failed to get rate from DB for {code}: {e}")
    
    # Fallback to hardcoded rates
    rate = FALLBACK_RATES.get(code, 1.0)
    print(f"DEBUG: Using fallback rate for {code}: {rate}")
    return rate
