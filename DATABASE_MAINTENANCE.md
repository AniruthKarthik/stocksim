# Database Maintenance & Data Refresh Guide

This document explains the StockSim database architecture and how to manage data synchronization during development and production deployment.

## 🏗 Database Architecture

The system uses a PostgreSQL database with two primary data tables and a maintenance log:

1. **`assets`**: Registry of all tradable instruments (Stocks, ETFs, Crypto, Commodities).
2. **`prices`**: Time-series historical daily data for all assets.
3. **`data_refresh_log`**: A tracking table that records when each category was last updated to prevent redundant API calls.

---

## 🔄 Automated Refresh System

We use an **Incremental Refresh** strategy. Instead of downloading full histories every time, the system checks the latest date available in the database for each ticker and only fetches the "gap" between that date and today.

### Maintenance Script
- **Path:** `backend/db_load/refresh_incremental.py`
- **Command:** `python3 backend/db_load/refresh_incremental.py`

### Rules of Operation
*   **Once-per-day:** Each asset category (e.g., `stocks`) will only run once per calendar day. Subsequent runs on the same day will exit gracefully.
*   **Gap Filling:** If the script hasn't been run for a week, it will automatically detect the 7-day gap and download exactly those missing days.
*   **Idempotency:** Uses `UPSERT` logic. If data already exists for a specific date, it is updated; if not, it is inserted.

---

## 🚀 Deployment Workflow

Follow these steps when deploying to a new environment or performing weekly maintenance.

### 1. Initial Environment Setup
Ensure your environment variables are configured in `.env`:
```bash
DB_NAME=stocksim
DB_USER=stocksim
DB_PASSWORD=your_password
DB_HOST=localhost
```

### 2. Schema Initialization
If starting with a fresh database, apply the schema first:
```bash
psql -d stocksim -f stocksim_schema.sql
```

### 3. Population (New Deployment)
On a first-time deployment, run the refresh script to populate the database with the tickers listed in `data/*.txt`:
```bash
python3 backend/db_load/refresh_incremental.py
```
*Note: The first run will take longer as it downloads full historical data (2000-present).*

### 4. Continuous Maintenance
To keep the simulation "live" with current market data, the refresh script should be executed once every 24 hours.

**Manual Update:**
```bash
cd /path/to/project
source env/bin/activate
python3 backend/db_load/refresh_incremental.py
```

**Production Automation (Crontab):**
To automate this on a Linux server, add a cron job to run every night at midnight:
```bash
0 0 * * * cd /home/user/site && /home/user/site/env/bin/python3 backend/db_load/refresh_incremental.py >> /home/user/site/refresh.log 2>&1
```

---

## 🛠 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Category 'stocks' already refreshed today` | Tracking log hit | To force a re-run, delete the log entry: `DELETE FROM data_refresh_log WHERE category = 'stocks' AND last_run = CURRENT_DATE;` |
| `Missing price data for <Date>` | Market holiday / weekend | The system automatically looks for the "Last Known Price" (previous trading day) if an exact date is missing. |
| `Too many requests` | Yahoo Finance throttling | The script includes a 3x retry policy and sleeps between batches. Wait 15 minutes and try again. |

---

## 📄 Standard CSV Format
If manually importing data, ensure the CSV follows this structure:
`date, open, high, low, close, adj_close, volume`
*(Date format: YYYY-MM-DD)*
