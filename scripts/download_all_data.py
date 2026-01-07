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
if os.getenv("DATABASE_URL"):
    DB_DSN = os.getenv("DATABASE_URL")
    DB_CONFIG = {} # Not used when DSN is present
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
            "failed": 0
        }

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
                    # Strip comments (anything after #)
                    clean_line = line.split('#')[0].strip()
                    if clean_line:
                        tickers.append(clean_line)
            # Clean symbols for Yahoo (replace '.' with '-') and remove duplicates
            return sorted(list(set([t.replace('.', '-') for t in tickers])))
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return []

    def download_data(self, ticker, start_date="2023-01-01"):
        """Downloads historical data for a ticker with retries."""
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
                
                # Required columns
                required = ['date', 'close', 'adj_close', 'volume']
                for col in required:
                    if col not in data.columns:
                        # If volume is missing (some indices/mutual funds), fill with 0
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
        df.to_csv(csv_path, index=False)
        return csv_path

    def load_to_db(self, ticker, asset_type, df, yahoo_ticker=None):
        """Loads data into PostgreSQL using upsert logic."""
        if yahoo_ticker is None:
            yahoo_ticker = ticker

        conn = None
        try:
            if DB_DSN:
                conn = psycopg2.connect(dsn=DB_DSN, sslmode=os.getenv("DB_SSLMODE", "require"))
            else:
                conn = psycopg2.connect(**DB_CONFIG)
            
            cur = conn.cursor()

            # 1. Fetch real company name if possible
            display_name = ticker.upper()
            try:
                # Check if we already have a professional name first
                cur.execute("SELECT name FROM assets WHERE symbol = %s", (ticker,))
                existing = cur.fetchone()
                
                if existing and existing[0] != ticker.capitalize() and existing[0] != ticker.upper():
                    display_name = existing[0]
                else:
                    info = yf.Ticker(yahoo_ticker).info
                    display_name = info.get('longName') or info.get('shortName') or display_name
            except:
                pass

            # 2. Ensure asset exists with real name
            cur.execute(
                """INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) 
                   ON CONFLICT (symbol) DO UPDATE SET 
                    name = CASE WHEN EXCLUDED.name != EXCLUDED.symbol THEN EXCLUDED.name ELSE assets.name END,
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

        logger.info(f"Found {len(ticker_files)} ticker files.")

        for file_path in ticker_files:
            asset_type = self.get_asset_type(file_path.name)
            tickers = self.read_tickers(file_path)
            
            logger.info(f"--- Processing {file_path.name} (Type: {asset_type}) | {len(tickers)} tickers ---")

            for i, ticker in enumerate(tickers):
                self.summary["attempted"] += 1
                
                # Special handling for Crypto: Use clean symbol for storage, -USD for Yahoo
                yahoo_ticker = ticker
                if asset_type == 'crypto' and not ticker.endswith('-USD'):
                    yahoo_ticker = f"{ticker}-USD"
                
                logger.info(f"[{asset_type}] {i+1}/{len(tickers)}: {ticker} (Fetch: {yahoo_ticker})")
                
                df = self.download_data(yahoo_ticker)
                if df is None:
                    logger.warning(f"No data for {ticker}, skipping.")
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
                if (i + 1) % 5 == 0:
                    time.sleep(0.5)

        self.print_summary()

    def print_summary(self):
        logger.info("=" * 30)
        logger.info("REFRESH SYSTEM SUMMARY")
        logger.info(f"Files Processed:   {len(list(BASE_DATA_DIR.glob('*_tickers.txt')))}")
        logger.info(f"Total Attempted:   {self.summary['attempted']}")
        logger.info(f"Successfully DL:   {self.summary['downloaded']}")
        logger.info(f"Successfully Load: {self.summary['loaded']}")
        logger.info(f"Skipped:           {self.summary['skipped']}")
        logger.info(f"Failed Load:       {self.summary['failed']}")
        logger.info("=" * 30)

if __name__ == "__main__":
    refresher = StockRefresher()
    refresher.run()