# Project Structure

This document outlines the organization of the StockSim codebase.

## Directory Layout

```text
/home/ani/site/
├── README.md                    # Main documentation
├── deploy.md                    # Deployment guide
├── envex.md                     # Environment variable reference
├── docker-compose.yml           # Docker orchestration (optional)
├── setupneon.txt                # Full SQL script for Neon DB setup
│
├── backend/                     # Python FastAPI Backend
│   ├── main.py                  # App entry point & API routes
│   ├── game_engine.py           # Core simulation logic (Time travel, budget)
│   ├── db_portfolio.py          # Portfolio & Transaction DB operations
│   ├── db_prices.py             # Asset price fetching & caching
│   ├── db_currency.py           # Currency conversion logic
│   ├── db_conn.py               # Database connection pool
│   ├── portfolio_schema.sql     # Database schema definition
│   └── requirements.txt         # Python dependencies
│
├── frontend/                    # Next.js Frontend
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Landing page
│   │   ├── dashboard/           # User dashboard
│   │   └── market/              # Market & Asset details
│   ├── components/              # Reusable UI components
│   ├── context/                 # React Context (Currency, State)
│   ├── lib/                     # Utilities (API client)
│   └── public/                  # Static assets
│
├── data/                        # Historical Data (CSV)
│   └── stocks/                  # Stock price data
│
└── scripts/                     # Maintenance Scripts
    ├── download_all_data.py     # Fetch data from Yahoo Finance
    └── load_local_csvs.py       # Import CSV data to DB
```

## Key Flows
1.  **User Creation:** `frontend` -> `POST /users` -> `backend` -> `DB (users table)`
2.  **Simulation Start:** `frontend` -> `POST /simulation/start` -> `backend` -> `DB (game_sessions table)`
3.  **Trading:** `frontend` -> `POST /portfolio/buy` -> `backend` -> `DB (transactions table)` -> `DB (portfolios table update)`