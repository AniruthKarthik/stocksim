# Stock Refresh System (Yahoo Finance -> Postgres)

This system provides a reliable, idempotent way to download historical stock data and load it into the StockSim database.

## Features
- **Dynamic Ticker List:** Fetches the current S&P 500 list from Wikipedia.
- **Robust Downloads:** Includes 3x retries and throttling protection.
- **Idempotent Loading:** Uses PostgreSQL `ON CONFLICT` (upsert) to ensure no duplicate price records are created, even if the script is run multiple times for the same date range.
- **Error Tolerance:** If one stock fails to download or load, the script continues to the next and provides a summary at the end.

## Requirements
Ensure you have the following Python packages installed:
```bash
pip install yfinance pandas psycopg2-binary lxml requests
```

## Directory Structure
- **Script:** `backend/db_load/refresh_stocks.py`
- **CSV Data:** `data/stocks/` (Generated automatically)
- **Logs:** `stock_refresh.log`

## Database Schema Support
The script works with the existing schema:
- `assets(id, symbol, name, type)`
- `prices(id, asset_id, date, close, adj_close, volume)`

## How It Avoids Duplicates
The script uses the `prices_assetid_date_key` UNIQUE constraint defined in the schema. 
When loading data, it executes an `INSERT ... ON CONFLICT (asset_id, date) DO UPDATE` query. This means:
1. If a price for a specific asset on a specific date **does not exist**, a new record is created.
2. If a price for that asset on that date **already exists**, the existing record is updated with the latest values (Close, Adj Close, Volume).
3. This allows you to re-run the script for overlapping date ranges (e.g., fetching "2000 to today" every week) without ever creating duplicate rows.

## Usage
Run the script from the project root:
```bash
python3 backend/db_load/refresh_stocks.py
```

## Environment Variables
The script uses variables from your `.env` file:
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
