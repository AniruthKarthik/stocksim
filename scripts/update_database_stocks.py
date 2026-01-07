#!/usr/bin/env python3
import os
import time
import logging
import pandas as pd
import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configuration
if os.getenv("DATABASE_URL"):
    # Strip potential 'psql ' prefix if user copied full command
    raw_url = os.getenv("DATABASE_URL")
    if raw_url.strip().startswith("psql"):
        raw_url = raw_url.replace("psql", "").strip()
    if (raw_url.startswith("'") and raw_url.endswith("'")) or (raw_url.startswith('"') and raw_url.endswith('"')):
        raw_url = raw_url[1:-1]
        
    DB_DSN = raw_url
    DB_CONFIG = {} 
else:
    DB_DSN = None
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
        logging.FileHandler("refresh_system.log"),
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
            "failed": 0,
            "up_to_date": 0
        }
        self.existing_data = {}

    def get_db_conn(self):
        if DB_DSN:
            return psycopg2.connect(dsn=DB_DSN, sslmode=os.getenv("DB_SSLMODE", "require"))
        else:
            return psycopg2.connect(**DB_CONFIG)

    def fetch_existing_data(self):
        """Fetches the latest available date for all assets in the database."""
        logger.info("Fetching existing data from database...")
        conn = None
        try:
            conn = self.get_db_conn()
            cur = conn.cursor()
            query = """
                SELECT a.symbol, MAX(p.date) 
                FROM assets a
                JOIN prices p ON a.id = p.asset_id
                GROUP BY a.symbol
            """
            cur.execute(query)
            rows = cur.fetchall()
            for symbol, date_obj in rows:
                self.existing_data[symbol] = date_obj
            logger.info(f"Found existing data for {len(self.existing_data)} assets.")
        except Exception as e:
            logger.error(f"Error fetching existing data: {e}")
        finally:
            if conn: conn.close()

    def get_asset_type(self, filename):
        """Maps filename to asset type."""
        name = filename.lower()
        if 'crypto' in name: return 'crypto'
        if 'commodit' in name: return 'commodities'
        if 'etf' in name: return 'etfs'
        if 'mutualfund' in name: return 'mutualfunds'
        if 'sp500' in name or 'stocks' in name: return 'stocks'
        return 'stocks' # default

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

    def download_data(self, ticker, start_date="2000-01-01"):
        """Downloads historical data for a ticker with retries."""
        # Validate start_date is not in the future
        try:
            start_dt = datetime.strptime(str(start_date), "%Y-%m-%d").date()
            if start_dt >= datetime.now().date():
                return None # Up to date
        except:
            pass

        for attempt in range(3):
            try:
                # Use a specific interval if needed, but default is daily
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
                for col in required:
                    if col not in data.columns:
                        if col == 'volume': data['volume'] = 0
                        else: return None 
                
                return data[required]
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {ticker}: {e}")
                time.sleep(1 * (attempt + 1))
        return None

    def save_to_csv(self, ticker, asset_type, df):
        """Saves dataframe to local CSV in type-specific folder."""
        target_dir = BASE_DATA_DIR / asset_type
        target_dir.mkdir(parents=True, exist_ok=True)
        csv_path = target_dir / f"{ticker}.csv"
        
        # If file exists, we might want to append, but for simplicity we overwrite 
        # or merge. Since we might have partial data, merging is complex.
        # For this script, we just save what we downloaded (latest chunk) 
        # OR we could read existing CSV and append.
        # Given we rely on DB, CSV is backup. Let's just overwrite with the new chunk 
        # effectively making CSV partial. 
        # Requirement says "add only latest", so downloading only latest means df is small.
        # We should probably append to CSV if exists.
        
        mode = 'w'
        header = True
        if csv_path.exists():
            mode = 'a'
            header = False
            
        df.to_csv(csv_path, mode=mode, header=header, index=False)
        return csv_path

    def load_to_db(self, ticker, asset_type, df, yahoo_ticker=None):
        """Loads data into PostgreSQL using upsert logic."""
        if yahoo_ticker is None:
            yahoo_ticker = ticker

        conn = None
        try:
            conn = self.get_db_conn()
            cur = conn.cursor()

            # 1. Fetch real company name if possible
            display_name = ticker.upper()
            
            # Optimization: Only fetch name if we are inserting a NEW asset
            # Use cached existing_data check or just simple select
            cur.execute("SELECT name FROM assets WHERE symbol = %s", (ticker,))
            existing = cur.fetchone()
            
            if existing:
                display_name = existing[0]
            else:
                try:
                    info = yf.Ticker(yahoo_ticker).info
                    display_name = info.get('longName') or info.get('shortName') or display_name
                except:
                    pass

            # 2. Ensure asset exists with real name
            cur.execute(
                """INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) 
                   ON CONFLICT (symbol) DO UPDATE SET 
                    type = EXCLUDED.type
                   RETURNING id""",
                (ticker, display_name, asset_type)
            )
            asset_id = cur.fetchone()[0]

            # 3. Prepare data
            df = df.dropna(subset=['date', 'close'])
            values = []
            for _, row in df.iterrows():
                values.append((
                    asset_id,
                    row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10],
                    float(row['close']),
                    float(row['adj_close']),
                    int(row['volume']) if not pd.isna(row['volume']) else 0
                ))

            if not values:
                return True

            # 4. Upsert into prices
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
        ticker_files = list(BASE_DATA_DIR.glob("*_tickers.txt"))
        if not ticker_files:
            logger.error("No ticker files found in data/ folder (*_tickers.txt)")
            return

        # 1. Fetch State
        self.fetch_existing_data()

        logger.info(f"Found {len(ticker_files)} ticker files.")

        for file_path in ticker_files:
            asset_type = self.get_asset_type(file_path.name)
            tickers = self.read_tickers(file_path)
            
            logger.info(f"--- Processing {file_path.name} (Type: {asset_type}) | {len(tickers)} tickers ---")

            for i, ticker in enumerate(tickers):
                self.summary["attempted"] += 1
                
                # Determine start date
                start_date = "2000-01-01"
                last_date = self.existing_data.get(ticker)
                
                if last_date:
                    # Start from the next day
                    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    logger.info(f"[{asset_type}] {i+1}/{len(tickers)}: {ticker} exists. Updating from {start_date}...")
                else:
                    logger.info(f"[{asset_type}] {i+1}/{len(tickers)}: {ticker} new. Full download...")

                # Special handling for Crypto
                yahoo_ticker = ticker
                if asset_type == 'crypto' and not ticker.endswith('-USD'):
                    yahoo_ticker = f"{ticker}-USD"
                
                df = self.download_data(yahoo_ticker, start_date=start_date)
                
                if df is None:
                    if last_date:
                         logger.info(f"  -> {ticker} is up to date.")
                         self.summary["up_to_date"] += 1
                    else:
                        logger.warning(f"  -> No data for {ticker}, skipping.")
                        self.summary["skipped"] += 1
                    continue
                
                self.summary["downloaded"] += 1
                self.save_to_csv(ticker, asset_type, df)
                
                success = self.load_to_db(ticker, asset_type, df, yahoo_ticker=yahoo_ticker)
                if success:
                    self.summary["loaded"] += 1
                else:
                    self.summary["failed"] += 1
                
                # Small sleep to be nice to Yahoo
                if (i + 1) % 10 == 0:
                    time.sleep(0.5)

        self.print_summary()

    def print_summary(self):
        logger.info("=" * 30)
        logger.info("UPDATE DATABASE SUMMARY")
        logger.info(f"Total Attempted:   {self.summary['attempted']}")
        logger.info(f"Up to Date:        {self.summary['up_to_date']}")
        logger.info(f"Downloaded (New):  {self.summary['downloaded']}")
        logger.info(f"Successfully Load: {self.summary['loaded']}")
        logger.info(f"Skipped/Empty:     {self.summary['skipped']}")
        logger.info(f"Failed Load:       {self.summary['failed']}")
        logger.info("=" * 30)

if __name__ == "__main__":
    refresher = StockRefresher()
    refresher.run()
