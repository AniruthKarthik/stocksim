import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime

# ================= CONFIGURATION =================
DATA_DIR = Path("data")
START_DATE = "2000-01-01"
END_DATE = datetime.today().strftime('%Y-%m-%d')

# Define assets: Group -> List of (Ticker, Filename)
ASSETS = {
    "commodities": [
        ("GC=F", "gold"),
        ("SI=F", "silver"),
    ],
    "crypto": [
        ("BTC-USD", "bitcoin"),
        ("ETH-USD", "ethereum"),
        ("XRP-USD", "xrp"),
        ("SOL-USD", "solana"),
        ("DOGE-USD", "dogecoin"),
    ],
    "stocks": [
        ("AAPL", "apple"),
        ("NVDA", "nvidia"),
        ("MSFT", "microsoft"),
        ("TSLA", "tesla"),
        ("AMZN", "amazon"),
    ],
    "etfs": [
        ("VOO", "voo_sp500"),
        ("SPY", "spy_sp500"),
        ("QQQ", "qqq_nasdaq"),
        ("VTI", "vti_total_market"),
        ("SCHD", "schd_dividend"),
    ],
    "mutual_funds": [
        ("VTSAX", "vtsax_total_market"),
        ("VFIAX", "vfiax_sp500"),
        ("SWPPX", "swppx_sp500"),
    ],
}

def download_and_save(ticker: str, name: str, group: str):
    """
    Downloads historical data for a single ticker and saves it to a CSV file.
    """
    print(f"Downloading {ticker} ({group}/{name}) ...")

    try:
        df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
    except Exception as e:
        print(f"  Error downloading {ticker}: {e}")
        return

    # Basic check if data exists
    if df is None or df.empty:
        print(f"  No data found for {ticker}")
        return

    # 1. Flatten MultiIndex columns (common in new yfinance versions)
    #    e.g. ('Close', 'AAPL') -> 'Close'
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    # 2. Reset index to move 'Date' from index to a column
    df.reset_index(inplace=True)

    # 3. Handle specific columns and missing Adj Close
    #    Desired columns: date, open, high, low, close, adj_close, volume
    
    # If Adj Close exists, use it. Otherwise, assume Close = Adj Close.
    if "Adj Close" in df.columns:
        # Select and reorder
        required_cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        # Ensure all columns exist before selecting (Volume sometimes missing for indices)
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            # If Volume is missing (common for some indices/funds), fill with 0
            if "Volume" in missing_cols:
                df["Volume"] = 0
            else:
                 print(f"  Missing columns {missing_cols} for {ticker}")
                 return
        
        df = df[required_cols]
        df.columns = ["date", "open", "high", "low", "close", "adj_close", "volume"]
        
    else:
        # Fallback: Use Close as Adj Close
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
             if "Volume" in missing_cols:
                df["Volume"] = 0
             else:
                print(f"   Missing columns {missing_cols} for {ticker}")
                return

        df = df[required_cols]
        df["Adj Close"] = df["Close"]
        # Rename to lowercase
        df.columns = ["date", "open", "high", "low", "close", "volume", "adj_close"]
        # Reorder to match standard
        df = df[["date", "open", "high", "low", "close", "adj_close", "volume"]]

    # 4. Create output directory
    out_dir = DATA_DIR / group
    out_dir.mkdir(parents=True, exist_ok=True)

    # 5. Save to CSV
    out_file = out_dir / f"{name}.csv"
    df.to_csv(out_file, index=False)
    print(f"  ✔ saved → {out_file}")


def main():
    print(f"Starting bulk download...")
    print(f"Output Directory: {DATA_DIR.resolve()}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print("-" * 40)

    for group, items in ASSETS.items():
        for ticker, name in items:
            download_and_save(ticker, name, group)

    print("-" * 40)
    print("All downloads completed.")

if __name__ == "__main__":
    main()
