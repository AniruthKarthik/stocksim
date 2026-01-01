# StockSim Backend Overview

This document provides a technical overview of the StockSim backend, including its structure, database schema, and API endpoints.

## 1. Project Structure

```
backend/
├── main.py              # FastAPI application entry point and route definitions.
├── simulator.py         # Business logic for the investment simulator.
├── db_prices.py         # Database access for Asset and Price data.
├── db_portfolio.py      # Database access for User, Portfolio, and Transaction data.
├── test_full_system.py  # Comprehensive test suite for backend verification.
├── db/
│   └── loadCsvToDb.py   # Script to load historical price data from CSVs into the DB.
└── portfolio_schema.sql # SQL definitions for the new portfolio system tables.
data/                    # Directory containing historical CSV data for assets.
stocksim_schema.sql      # Initial schema for Assets and Prices.
```

## 2. Database Schema

The database consists of two main modules: Market Data and User Data.

### Market Data Tables
*   **`assets`**: Stores metadata about tradable assets.
    *   `id` (PK), `symbol` (Unique), `name`, `type`, `currency`.
*   **`prices`**: Stores historical price data.
    *   `id` (PK), `asset_id` (FK -> assets), `date`, `close`, `adj_close`, `volume`.
    *   Unique constraint on `(asset_id, date)`.

### User & Portfolio Tables (New)
*   **`users`**: Stores user identities.
    *   `id` (PK), `username` (Unique).
*   **`portfolios`**: Stores user portfolios.
    *   `id` (PK), `user_id` (FK -> users), `name`, `cash_balance`.
*   **`transactions`**: Records all buy/sell actions.
    *   `id` (PK), `portfolio_id` (FK -> portfolios), `asset_id` (FK -> assets), `type` (BUY/SELL), `quantity`, `price_per_unit`, `date`.

## 3. Backend Workflow

### Request Flow
1.  **Request**: Client sends HTTP request (e.g., `POST /portfolio/buy`) to FastAPI (`main.py`).
2.  **Validation**: Pydantic models validate the JSON payload (types, required fields).
3.  **Database Operation**:
    *   Controller calls `db_portfolio.py` or `db_prices.py`.
    *   Connection is established via `psycopg2`.
    *   Logic validates constraints (e.g., sufficient funds).
    *   Transaction is committed or rolled back on error.
4.  **Response**: JSON response is returned to the client (success data or error message).

## 4. Function-Level Explanations

### `backend/db_prices.py`
*   **`get_price(symbol, date)`**:
    *   **Input**: Stock symbol (str), Date (YYYY-MM-DD).
    *   **Output**: Adjusted Close Price (float) or `None`.
    *   **Logic**: Tries to find exact date match. If missing (weekend/holiday), searches for the nearest *future* trading day within 7 days.
*   **`connect()`**: safely creates and returns a DB connection.

### `backend/db_portfolio.py`
*   **`add_transaction(portfolio_id, symbol, txn_type, quantity, date)`**:
    *   **Logic**:
        1.  Fetches asset price for the given date.
        2.  Locks portfolio row.
        3.  Checks balance (for BUY) or calculates holdings (for SELL).
        4.  Updates `cash_balance` and inserts row into `transactions`.
*   **`get_portfolio_value(portfolio_id, date)`**:
    *   **Logic**: Reconstructs portfolio history to determine value. (Currently implemented as: historical cash flow + value of assets at that date).

### `backend/db/loadCsvToDb.py`
*   **`load_prices(asset_id, csv_path)`**:
    *   Reads CSV, cleans data, and bulk inserts into `prices` table using `executemany` for performance.

## 5. API Documentation

### Market Data
*   **GET /price**
    *   **Params**: `symbol`, `date`
    *   **Example**: `GET /price?symbol=AAPL&date=2023-01-01`
    *   **Response**: `{"symbol": "AAPL", "price": 150.23}`

*   **GET /simulate**
    *   **Params**: `amount`, `symbol`, `buy` (date), `sell` (date)
    *   **Response**: `{"future_value": 12500.50, ...}`

### Portfolio Management
*   **POST /users**
    *   **Body**: `{"username": "jdoe"}`
    *   **Response**: `{"user_id": 1}`

*   **POST /portfolio/create**
    *   **Body**: `{"user_id": 1, "name": "Retirement"}`
    *   **Response**: `{"id": 1, "cash_balance": 10000.0}`

*   **POST /portfolio/buy**
    *   **Body**: `{"portfolio_id": 1, "symbol": "AAPL", "quantity": 10, "date": "2023-01-05"}`
    *   **Response**: `{"status": "success", "new_balance": ...}`

*   **GET /portfolio/{id}**
    *   **Response**: Portfolio details including current holdings.

## 6. Setup + Run Instructions

1.  **Environment**:
    *   Create `.env` file with `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`.
2.  **Database**:
    *   Ensure PostgreSQL is running.
    *   Run `python3 backend/init_db.py` to create tables.
3.  **Load Data**:
    *   Run `python3 backend/db/loadCsvToDb.py` to import CSVs.
4.  **Start API**:
    *   `uvicorn backend.main:app --reload`

## 7. Testing

To verify the system integrity, run the comprehensive test suite:
```bash
python3 backend/test_full_system.py
```
This suite verifies:
*   Price fetching (including weekend fallbacks).
*   Investment simulator logic.
*   Full portfolio lifecycle (User creation -> Portfolio creation -> Buy -> Sell -> Value calculation).

## 8. Changes Made & Why

### Fix: Loader Column Names & Performance
*   **Problem**: `loadCsvToDb.py` used incorrect column names (`assetid` vs `asset_id`) and opened a new DB connection for every row.
*   **Change**: Corrected SQL column names and used `executemany` with a single connection.
*   **Reason**: To prevent SQL errors and drastically reduce load time (from minutes to seconds).

### Improvement: Price Fetching Fallback
*   **Problem**: `get_price` returned `None` if a date fell on a weekend, causing simulation crashes.
*   **Change**: Added logic to look ahead up to 7 days for the next valid trading price.
*   **Reason**: Ensures smoother user experience and valid simulations even with imperfect date inputs.

### Feature: Portfolio System
*   **Problem**: No way to track persistent user portfolios.
*   **Change**: Added `users`, `portfolios`, and `transactions` tables and corresponding API endpoints.
*   **Reason**: Core requirement for a full "simulation" backend beyond simple calculator logic.

### Refactor: Safe DB Connections
*   **Problem**: Potential for connection leaks in original scripts.
*   **Change**: Added `try...finally` blocks to ensure `conn.close()` is always called.
*   **Reason**: Prevent "too many clients" errors in PostgreSQL during heavy usage.

### Tooling: Test Suite
*   **Problem**: No automated way to verify backend integrity.
*   **Change**: Added `backend/test_full_system.py`.
*   **Reason**: Ensures all functions work correctly after updates and deployments.