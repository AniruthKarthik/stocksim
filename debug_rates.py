import yfinance as yf
import pandas as pd

def debug_fetch():
    to_fetch = {
        'EUR': 'EUR=X', 
        'GBP': 'GBP=X', 
        'AUD': 'AUDUSD=X', 
        'JPY': 'JPY=X', 
        'CAD': 'CAD=X', 
        'INR': 'INR=X'  
    }
    inverse_quotes = ['EUR', 'GBP', 'AUD']
    
    tickers_str = " ".join(to_fetch.values())
    data = yf.download(tickers_str, period="1d", progress=False)['Close']
    
    print("Raw Data:")
    print(data.tail(1))
    
    rates = {'USD': 1.0}
    
    def get_val(ticker):
        try:
            if isinstance(data, pd.DataFrame):
                val = data[ticker].iloc[-1]
            else:
                val = data.iloc[-1]
            return float(val)
        except Exception as e:
            print(f"Error getting val for {ticker}: {e}")
            return None

    for code, ticker in to_fetch.items():
        val = get_val(ticker)
        print(f"Code: {code}, Ticker: {ticker}, Val: {val}, In inverse: {code in inverse_quotes}")
        if val and val > 0:
            if code in inverse_quotes:
                rate = 1.0 / val
                print(f"  Result (Inversed): {rate}")
                rates[code] = rate
            else:
                print(f"  Result (Direct): {val}")
                rates[code] = val
    return rates

print("Final Rates:", debug_fetch())
