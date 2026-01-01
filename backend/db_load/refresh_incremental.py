import os
import sys
import time
import logging
import pandas as pd
import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta, date

# Load environment variables
load_dotenv()

# Configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "stocksim"),
    "user": os.getenv("DB_USER", "stocksim"),
    "password": os.getenv("DB_PASSWORD", "stocksim"),
    "host": os.getenv("DB_HOST", "localhost")
}

BASE_DATA_DIR = Path("data")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("refresh_incremental.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IncrementalRefresher:
    def __init__(self):
        self.summary = {
            "tickers_checked": 0,
            "tickers_updated": 0,
            "skipped_up_to_date": 0,
            "errors": 0,
            "days_added": 0
        }
        self.today = date.today()

    def get_asset_type(self, filename):
        """Maps filename to asset type."""
        name = filename.lower()
        if 'crypto' in name: return 'crypto'
        if 'commodit' in name: return 'commodities'
        if 'etf' in name: return 'etfs'
        if 'mutualfund' in name: return 'mutualfunds'
        if 'sp500' in name or 'stocks' in name: return 'stocks'
        return 'stocks'

    def read_tickers(self, file_path):
        """Reads tickers from a local text file, handling comments."""
        try:
            tickers = []
            with open(file_path, 'r') as f:
                for line in f:
                    clean_line = line.split('#')[0].strip()
                    if clean_line:
                        tickers.append(clean_line)
            return sorted(list(set([t.replace('.', '-') for t in tickers])))
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return []

    def check_if_refreshed_today(self, category):
        """Checks tracking table if category was already refreshed today."""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM data_refresh_log WHERE category = %s AND last_run = %s",
                (category, self.today)
            )
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check refresh log: {e}")
            return False
        finally:
            if conn: conn.close()

    def log_refresh(self, category):
        """Updates tracking table after successful refresh."""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO data_refresh_log (category, last_run) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (category, self.today)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to update refresh log: {e}")
        finally:
            if conn: conn.close()

    def get_latest_date(self, ticker):
        """Finds the latest date present in prices table for that asset."""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # First, get asset_id
            cur.execute("SELECT id FROM assets WHERE symbol = %s", (ticker.upper(),))
            res = cur.fetchone()
            if not res:
                return None, None # New asset
            
            asset_id = res[0]
            
            # Get max date
            cur.execute("SELECT MAX(date) FROM prices WHERE asset_id = %s", (asset_id,))
            max_date = cur.fetchone()[0]
            
            return asset_id, max_date
        except Exception as e:
            logger.error(f"Failed to get latest date for {ticker}: {e}")
            return None, None
        finally:
            if conn: conn.close()

    def download_incremental(self, ticker, last_date):
        """Downloads missing dates from last_date + 1 to today."""
        start_date = "2000-01-01"
        if last_date:
            # If we have data, start from the next day
            start_date_obj = last_date + timedelta(days=1)
            
            # If the next day is already today or in the future, we are up to date
            if start_date_obj >= self.today:
                return "UP_TO_DATE"
            
            start_date = start_date_obj.strftime('%Y-%m-%d')

        for attempt in range(3):
            try:
                data = yf.download(ticker, start=start_date, progress=False)
                if data.empty:
                    return None
                
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
                time.sleep(1)
        return None

    def load_to_db(self, ticker, asset_type, df):
        """Loads data into PostgreSQL using upsert logic."""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Ensure asset exists
            cur.execute(
                """INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) 
                   ON CONFLICT (symbol) DO UPDATE SET type = EXCLUDED.type
                   RETURNING id""",
                (ticker.upper(), ticker.upper(), asset_type)
            )
            asset_id = cur.fetchone()[0]

            df = df.dropna(subset=['date', 'close'])
            values = []
            for _, row in df.iterrows():
                # Convert Timestamp to date string
                d_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10]
                values.append((
                    asset_id,
                    d_str,
                    float(row['close']),
                    float(row['adj_close']),
                    int(row['volume']) if not pd.isna(row['volume']) else 0
                ))

            if not values:
                return True

            upsert_query = """
                INSERT INTO prices (asset_id, date, close, adj_close, volume)
                VALUES %s
                ON CONFLICT (asset_id, date) DO UPDATE SET 
                    close = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume = EXCLUDED.volume
            """
            execute_values(cur, upsert_query, values)
            conn.commit()
            
            self.summary["days_added"] += len(values)
            return True
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"DB load failed for {ticker}: {e}")
            return False
        finally:
            if conn: conn.close()

    def run(self):
        ticker_files = list(BASE_DATA_DIR.glob("*_tickers.txt"))
        if not ticker_files:
            logger.error("No ticker files found in data/ (*_tickers.txt)")
            return

        for file_path in ticker_files:
            category = self.get_asset_type(file_path.name)
            
            # Rule: Only update once per day per category
            if self.check_if_refreshed_today(category):
                logger.info(f"Category '{category}' already refreshed today. Skipping.")
                continue

            tickers = self.read_tickers(file_path)
            logger.info(f"--- Refreshing Category: {category} ({len(tickers)} tickers) ---")

            category_updated = False
            for ticker in tickers:
                self.summary["tickers_checked"] += 1
                
                # 1. Find latest date
                asset_id, last_date = self.get_latest_date(ticker)
                
                # 2. Download incremental data
                df = self.download_incremental(ticker, last_date)
                
                if df == "UP_TO_DATE":
                    self.summary["skipped_up_to_date"] += 1
                    continue
                
                if df is None:
                    # Could be weekend or actual failure
                    # If last_date is Friday and today is Sunday, Yahoo returns empty
                    if last_date and (self.today - last_date).days <= 3:
                        self.summary["skipped_up_to_date"] += 1
                    else:
                        logger.error(f"Failed to fetch data for {ticker}")
                        self.summary["errors"] += 1
                    continue

                # 3. Load to DB
                if self.load_to_db(ticker, category, df):
                    self.summary["tickers_updated"] += 1
                    category_updated = True
                else:
                    self.summary["errors"] += 1

            # Log category refresh completion
            self.log_refresh(category)
            logger.info(f"Finished category: {category}")

        self.print_summary()

    def print_summary(self):
        print("\n" + "="*40)
        print("INCREMENTAL REFRESH SUMMARY")
        print(f"Date:               {self.today}")
        print(f"Total Tickers Checked: {self.summary['tickers_checked']}")
        print(f"Tickers Updated:       {self.summary['tickers_updated']}")
        print(f"Skipped (Up to date):  {self.summary['skipped_up_to_date']}")
        print(f"Errors encountered:    {self.summary['errors']}")
        print(f"Total Price Points:    {self.summary['days_added']}")
        print("="*40)

if __name__ == "__main__":
    refresher = IncrementalRefresher()
    refresher.run()
