# Project Structure & Deployment Overview: Stock Simulator

I am looking for suggestions on how to deploy this full-stack application. Below is the project structure and technical stack details.

## 🚀 Technical Stack
- **Frontend:** Next.js 15 (TypeScript, Tailwind CSS, App Router)
- **Backend:** Python 3.9 (FastAPI, Uvicorn)
- **Database:** PostgreSQL 15
- **Containerization:** Docker & Docker Compose
- **Data Source:** Yahoo Finance (via Python scripts) and local CSV datasets

## 📂 Project Directory Structure
```text
/home/ani/site/
├── docker-compose.yml           # Orchestrates DB, Backend, and Frontend
├── stocksim_schema.sql          # Main database schema
├── requirements.txt             # Python dependencies
├── backend/
│   ├── main.py                  # FastAPI Entry point
│   ├── Dockerfile               # Python slim-based image
│   ├── portfolio_schema.sql     # Portfolio-specific DB schema
│   ├── game_engine.py           # Core simulator logic
│   ├── db_prices.py             # Database interaction for price data
│   └── db_load/                 # Scripts to populate DB from CSVs
├── frontend/
│   ├── app/                     # Next.js App Router (Dashboard, Market, etc.)
│   ├── components/              # UI Components (Modals, Navbar, etc.)
│   ├── Dockerfile               # Node.js Alpine-based image
│   ├── package.json             # Frontend dependencies
│   └── next.config.ts           # Next.js configuration
├── data/                        # Historical CSV data (Stocks, ETFs, Crypto)
└── scripts/
    └── yahoo_finance.py         # Script to fetch live data
```

