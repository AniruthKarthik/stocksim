# StockSim Backend Overview

This document provides a technical overview of the StockSim backend, including its structure, database schema, game logic, and API endpoints.

## 1. Project Structure

```
backend/
├── main.py              # FastAPI application entry point. Handles HTTP requests.
├── game_engine.py       # Core logic for time travel, sessions, salary, and expenses.
├── simulator.py         # Stateless "what if" calculator logic.
├── db_prices.py         # Database access for Asset and Price data.
├── db_portfolio.py      # Database access for User, Portfolio, and Transaction data.
├── init_db.py           # Script to initialize database schema.
├── test_full_system.py  # Comprehensive test suite.
├── db/
│   └── loadCsvToDb.py   # Script to load historical price data from CSVs.
└── portfolio_schema.sql # SQL definitions for users, portfolios, transactions, and sessions.
data/                    # Directory containing historical CSV data.
```

## 2. Database Schema

The database consists of Market Data, User Data, and Game State.

### Market Data Tables
*   **`assets`**: Stores metadata about tradable assets.
    *   `id` (PK), `symbol` (Unique), `name`, `type`, `currency`.
*   **`prices`**: Stores historical price data.
    *   `id` (PK), `asset_id` (FK), `date`, `close`, `adj_close`, `volume`.
    *   Unique constraint on `(asset_id, date)`.

### User & Portfolio Tables
*   **`users`**: Stores user identities.
    *   `id` (PK), `username` (Unique).
*   **`portfolios`**: Stores user portfolios.
    *   `id` (PK), `user_id` (FK), `name`, `cash_balance`.
*   **`transactions`**: Records all buy/sell actions.
    *   `id` (PK), `portfolio_id` (FK), `asset_id` (FK), `type`, `quantity`, `price_per_unit`, `date`.

### Game State (New)
*   **`game_sessions`**: Tracks the simulation state for a portfolio.
    *   `id` (PK), `portfolio_id` (FK), `user_id` (FK).
    *   `start_date`: The real-world date where simulation began (e.g., 2010-01-01).
    *   `sim_date`: The current date inside the simulation.
    *   `monthly_salary`, `monthly_expenses`.
    *   `is_active`: Boolean flag (Only one active session per portfolio allowed).
    *   `created_at`: Timestamp.

## 3. Game Loop & Time Travel Logic

The backend now supports a stateful "Time Travel" mode.

### Workflow
1.  **Start Session**: User starts a simulation at a specific past date (e.g., 2010-01-01) with defined Salary and Expenses.
2.  **Trade**: User buys/sells assets. The system **automatically** uses the session's `sim_date` as the trade date.
3.  **Advance Time**: User requests to move forward (e.g., to 2010-04-01).
    *   System calculates months passed.
    *   `Cash Added = (Monthly Salary - Monthly Expenses) * Months Passed`.
    *   `sim_date` is updated.
4.  **Repeat**: User trades at the new date, then advances again.

### Session Lifecycle & Multiple Sessions
*   **Single Active Rule**: A portfolio can only have **one** active session at a time.
*   **Auto-Close**: Starting a new session **automatically deactivates** any previous session for that portfolio.
*   **History**: Old sessions remain in the database with `is_active = FALSE`. This allows users to review their past "runs".

## 4. Function-Level Explanations

### `backend/game_engine.py`
*   **`create_session(...)`**:
    *   Deactivates any existing active session for the portfolio.
    *   Creates a new active session row.
*   **`advance_time(portfolio_id, target_date)`**:
    *   Validates `target_date > current_sim_date`.
    *   Calculates full months passed.
    *   Updates `portfolios.cash_balance` by adding net income.
    *   Updates `game_sessions.sim_date`.
*   **`get_session(portfolio_id)`**: Returns the currently active session metadata.
*   **`list_sessions(user_id)`**: Returns a list of all sessions (active and inactive) for a user.

### `backend/main.py` (API Layer)
*   **`_resolve_trade_date(...)`**:
    *   If a session is active, forces the trade date to be `sim_date`.
    *   If no session, requires user to provide a date (Legacy/Manual mode).

## 5. API Documentation

### Simulation Control
*   **POST /simulation/start**
    *   **Body**: `{"user_id": 1, "portfolio_id": 1, "start_date": "2015-01-01", "monthly_salary": 5000, "monthly_expenses": 3000}`
    *   **Response**: `{"session_id": 1, "sim_date": "2015-01-01"}`
    *   *Effect*: Closes any old session, starts a new one.

*   **POST /simulation/forward**
    *   **Body**: `{"portfolio_id": 1, "target_date": "2015-04-01"}`
    *   **Response**: `{"status": "success", "months_passed": 3, "cash_added": 6000.0, "new_date": "2015-04-01"}`

*   **GET /simulation/status?portfolio_id=1**
    *   **Response**: `{"session": {...}, "portfolio_value": {...}}`

*   **GET /simulation/list?user_id=1**
    *   **Response**: `{"user_id": 1, "sessions": [{"id": 1, "is_active": false, ...}, {"id": 2, "is_active": true, ...}]}`

### Portfolio Management (Updated)
*   **POST /portfolio/buy**
    *   **Body**: `{"portfolio_id": 1, "symbol": "AAPL", "quantity": 10}` (Date optional if session active)
    *   **Response**: `{"status": "success", "new_balance": ...}`

*   **POST /portfolio/sell**
    *   Same as buy, checks holdings.

### Market Data
*   **GET /price?symbol=AAPL&date=2023-01-01**
*   **GET /simulate?amount=1000&symbol=AAPL&buy=2010-01-01&sell=2020-01-01** (Stateless calculator)

## 6. Bugs Found & Fixed
*   **Validation Script Crash**: The `validate_api_flow.py` script originally tried to start and kill the `uvicorn` process itself. This caused race conditions and connection errors.
    *   **Fix**: Updated the script to assume the server is already running and only perform HTTP requests.
*   **Constraint Error**: The `game_sessions` table originally had a `UNIQUE(portfolio_id)` constraint, preventing multiple sessions per portfolio.
    *   **Fix**: Dropped this constraint to allow multiple rows per portfolio (multiple historical sessions), relying on the application logic (and `is_active` flag) to enforce the "one active session" rule.

## 7. Setup + Run Instructions

1.  **Database**:
    *   Run `python -m backend.init_db` to apply the latest schema.
    *   *Note*: If you have an existing DB, you might need to manually drop the unique constraint: `ALTER TABLE game_sessions DROP CONSTRAINT game_sessions_portfolio_id_key;`.
2.  **Load Data** (If not done):
    *   Run `python backend/db/loadCsvToDb.py`.
3.  **Start API**:
    *   `uvicorn backend.main:app --reload`
4.  **Test**:
    *   `python -m backend.test_full_system`
    *   `python backend/validate_api_flow.py` (Ensure server is running first)