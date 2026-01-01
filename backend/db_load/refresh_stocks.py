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

    def get_tickers_from_file(self, file_path="data/sp500_tickers.txt"):
        """Reads tickers from a local text file."""
        try:
            logger.info(f"Reading ticker list from {file_path}...")
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File {file_path} not found. Falling back to curated list.")
                return CURATED_TICKERS
            
            with open(path, 'r') as f:
                # Read lines, strip whitespace, remove empty lines
                tickers = [line.strip() for line in f if line.strip()]
            
            # Clean symbols for Yahoo (replace '.' with '-')
            tickers = [t.replace('.', '-') for t in tickers]
            logger.info(f"Successfully retrieved {len(tickers)} tickers from file.")
            return tickers
        except Exception as e:
            logger.error(f"Failed to read tickers from file: {e}")
            return CURATED_TICKERS

    def download_data(self, ticker, start_date="2000-01-01"):
# ... (rest of the logic remains same) ...
        for attempt in range(3):
            try:
                data = yf.download(ticker, start=start_date, progress=False)
                if data.empty:
                    return None
                
                # Normalize column names
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
                data = data.reset_index()
                data.columns = [c.lower().replace(' ', '_') for c in data.columns]
                
                if 'adj_close' not in data.columns:
                    data['adj_close'] = data['close']
                
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

            # 1. Fetch real company name if possible
            display_name = ticker.capitalize()
            try:
                info = yf.Ticker(ticker).info
                display_name = info.get('longName') or info.get('shortName') or display_name
            except:
                pass

            # 2. Ensure asset exists with real name
            cur.execute(
                """INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) 
                   ON CONFLICT (symbol) DO UPDATE SET name = EXCLUDED.name 
                   RETURNING id""",
                (ticker, display_name, "stocks")
            )
            asset_id = cur.fetchone()[0]

            # 3. Prepare data for insertion
            df = df.dropna(subset=['date', 'close'])
            
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

    def run(self):
        tickers = self.get_tickers_from_file()
        # Merge with curated list and remove duplicates
        all_tickers = sorted(list(set(CURATED_TICKERS + tickers)))
        
        logger.info(f"Starting refresh for {len(all_tickers)} tickers...")

        for i, ticker in enumerate(all_tickers):
            self.summary["attempted"] += 1
            logger.info(f"[{i+1}/{len(all_tickers)}] Processing {ticker}...")
            
            df = self.download_data(ticker)
            if df is None:
                logger.warning(f"No data found for {ticker}, skipping.")
                self.summary["skipped"] += 1
                continue
            
            self.summary["downloaded"] += 1
            self.save_to_csv(ticker, df)
            
            success = self.load_to_db(ticker, df)
            if success:
                self.summary["loaded"] += 1
            else:
                self.summary["failed"] += 1
            
            if (i + 1) % 10 == 0:
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
    refresher.run()
