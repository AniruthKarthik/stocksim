# StockSim: Historical Market Simulator

StockSim is a full-stack time-travel trading simulator. It allows users to simulate trading strategies on historical data (Stocks, ETFs, Crypto) with a realistic portfolio management system.

## 🚀 Live Demo
- **Frontend:** [https://stocksim-log.onrender.com](https://stocksim-log.onrender.com)
- **Backend API:** [https://stocksim-backend.onrender.com](https://stocksim-backend.onrender.com) (or similar, check deployment)

## 🛠️ Tech Stack
- **Frontend:** Next.js 15 (React, TypeScript, Tailwind CSS)
- **Backend:** Python FastAPI (Uvicorn, Pydantic)
- **Database:** PostgreSQL (Neon Serverless)
- **Hosting:** Render (Web Services)

## 📂 Project Structure
- `frontend/`: Next.js application (UI, Charts, Dashboard).
- `backend/`: FastAPI application (Game Engine, DB Logic, Market Data).
- `data/`: CSV files containing historical market data.
- `scripts/`: Utilities for data fetching and database maintenance.

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (Local or Cloud)

### 1. Setup Environment Variables
See `envex.md` for details. Create `.env` in the root and `.env.local` in `frontend/`.

### 2. Start Backend
```bash
# Create virtual env
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run Server
uvicorn backend.main:app --reload
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

## 🚀 Deployment
We use **Neon** for the database and **Render** for hosting.
See [deploy.md](deploy.md) for step-by-step instructions.

## 📚 Documentation
- [Deployment Guide](deploy.md)
- [Project Structure](PROJECT_STRUCTURE.md)
- [Backend Overview](backend/BACKEND_OVERVIEW.md)
- [Frontend Overview](frontend/FRONTEND_OVERVIEW.md)
- [Database Maintenance](DATABASE_MAINTENANCE.md)
