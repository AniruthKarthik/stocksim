import os
import time
import logging
import pandas as pd
import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "stocksim"),
    "user": os.getenv("DB_USER", "stocksim"),
    "password": os.getenv("DB_PASSWORD", "stocksim"),
    "host": os.getenv("DB_HOST", "localhost")
}

DATA_DIR = Path("data/stocks")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Curated list of popular stocks
CURATED_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "JPM", "V", "MA", "BRK-B", "KO", "PEP", "MCD",
    "NFLX", "AMD", "INTC", "ORCL", "CRM", "COST",
    "WMT", "PG", "DIS", "HD", "BAC", "VZ", "ADBE"
]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stock_refresh.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StockRefresher:
    def __init__(self):
        self.summary = {
            "attempted": 0,
            "downloaded": 0,
            "loaded": 0,
            "skipped": 0,
            "failed": 0
        }

    def get_sp500_tickers(self):
        """Fetches S&P 500 tickers from Wikipedia, fallback to curated list."""
        try:
            logger.info("Fetching S&P 500 ticker list from Wikipedia...")
            table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
            df = table[0]
            tickers = df['Symbol'].tolist()
            # Clean symbols for Yahoo (replace '.' with '-')
            tickers = [t.replace('.', '-') for t in tickers]
            logger.info(f"Successfully retrieved {len(tickers)} tickers from S&P 500.")
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch dynamic S&P 500 list: {e}")
            logger.warning("Falling back to curated ticker list.")
            return CURATED_TICKERS

    def download_data(self, ticker, start_date="2000-01-01"):
        """Downloads historical data for a ticker with retries."""
        for attempt in range(3):
            try:
                data = yf.download(ticker, start=start_date, progress=False)
                if data.empty:
                    return None
                
                # Normalize column names
                # yfinance returns MultiIndex columns in recent versions, handle that
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
                data = data.reset_index()
                data.columns = [c.lower().replace(' ', '_') for c in data.columns]
                
                # Ensure adj_close exists
                if 'adj_close' not in data.columns:
                    data['adj_close'] = data['close']
                
                # Required columns for CSV/DB
                required = ['date', 'close', 'adj_close', 'volume']
                return data[required]
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")
                time.sleep(2 * (attempt + 1))
        return None

    def save_to_csv(self, ticker, df):
        """Saves dataframe to local CSV."""
        csv_path = DATA_DIR / f"{ticker}.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

    def load_to_db(self, ticker, df):
        """Loads data into PostgreSQL using upsert logic."""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # 1. Ensure asset exists
            cur.execute(
                "INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) ON CONFLICT (symbol) DO UPDATE SET symbol=EXCLUDED.symbol RETURNING id",
                (ticker, ticker.capitalize(), "stocks")
            )
            asset_id = cur.fetchone()[0]

            # 2. Prepare data for insertion
            # Filter out any rows with missing essential data
            df = df.dropna(subset=['date', 'close'])
            
            # Convert values to list of tuples
            values = []
            for _, row in df.iterrows():
                values.append((
                    asset_id,
                    row['date'].strftime('%Y-%m-%d'),
                    float(row['close']),
                    float(row['adj_close']),
                    int(row['volume'])
                ))

            # 3. Upsert into prices
            # We use ON CONFLICT to make it idempotent
            upsert_query = """
                INSERT INTO prices (asset_id, date, close, adj_close, volume)
                VALUES %s
                ON CONFLICT (asset_id, date) 
                DO UPDATE SET 
                    close = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume = EXCLUDED.volume
            """
            execute_values(cur, upsert_query, values)
            
            conn.commit()
            return True
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Database load failed for {ticker}: {e}")
            return False
        finally:
            if conn: conn.close()

    def run(self, limit=500):
        tickers = self.get_sp500_tickers()
        # Merge with curated list and remove duplicates
        all_tickers = sorted(list(set(CURATED_TICKERS + tickers)))
        
        # Limit the number of tickers
        target_tickers = all_tickers[:limit]
        
        logger.info(f"Starting refresh for {len(target_tickers)} tickers...")

        for i, ticker in enumerate(target_tickers):
            self.summary["attempted"] += 1
            logger.info(f"[{i+1}/{len(target_tickers)}] Processing {ticker}...")
            
            # Download
            df = self.download_data(ticker)
            if df is None:
                logger.warning(f"No data found for {ticker}, skipping.")
                self.summary["skipped"] += 1
                continue
            
            self.summary["downloaded"] += 1
            
            # Save CSV
            self.save_to_csv(ticker, df)
            
            # Load to DB
            success = self.load_to_db(ticker, df)
            if success:
                self.summary["loaded"] += 1
            else:
                self.summary["failed"] += 1
            
            # Throttling protection
            if (i + 1) % 10 == 0:
                logger.info("Taking a short break to respect API limits...")
                time.sleep(1)

        self.print_summary()

    def print_summary(self):
        logger.info("=" * 30)
        logger.info("STOCK REFRESH SUMMARY")
        logger.info(f"Total Attempted:   {self.summary['attempted']}")
        logger.info(f"Successfully DL:   {self.summary['downloaded']}")
        logger.info(f"Successfully Load: {self.summary['loaded']}")
        logger.info(f"Skipped:           {self.summary['skipped']}")
        logger.info(f"Failed Load:       {self.summary['failed']}")
        logger.info("=" * 30)

if __name__ == "__main__":
    refresher = StockRefresher()
    refresher.run(limit=500)
