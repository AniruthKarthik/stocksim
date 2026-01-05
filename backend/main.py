from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from .simulator import simulate_invest
from .db_prices import get_price, get_all_assets, get_price_history
from . import db_prices
from . import db_portfolio as portfolio
from . import db_currency
from . import game_engine
from .db_conn import get_db_connection

app = FastAPI()

# --- CORS Configuration ---
# Allow all for debugging
origins = ["*"]

print("DEBUG: Loading backend/main.py - Version 2.2 (Robust DB Connection)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class CreateUserRequest(BaseModel):
    username: str

class CreatePortfolioRequest(BaseModel):
    user_id: int
    name: str
    currency_code: Optional[str] = "USD"

class TradeRequest(BaseModel):
    portfolio_id: int
    symbol: str
    quantity: float
    date: Optional[str] = None

class ValueRequest(BaseModel):
    portfolio_id: int
    date: str

class StartSimRequest(BaseModel):
    user_id: int
    portfolio_id: int
    start_date: str # YYYY-MM-DD
    monthly_salary: float = 0
    monthly_expenses: float = 0

class ForwardSimRequest(BaseModel):
    portfolio_id: int
    target_date: str # YYYY-MM-DD

# --- Routes ---

@app.get("/")
def home():
    return {"status": "ok", "message": "StockSim Backend API"}

@app.get("/assets")
def get_assets(date: Optional[str] = None):
    assets = get_all_assets(date)
    print(f"DEBUG: Fetched {len(assets)} assets as of {date}")
    return assets

@app.get("/price/history")
def get_history(symbol: str, end_date: str):
    print(f"DEBUG: Fetching history for {symbol} until {end_date}")
    history = get_price_history(symbol.upper(), end_date)
    print(f"DEBUG: Found {len(history)} data points")
    return history

@app.get("/price")
def get_asset_price(symbol: str, date: str):
    print(f"DEBUG: Fetching price for {symbol} on {date}")
    price = get_price(symbol.upper(), date)
    if price is None:
        print(f"DEBUG: Price NOT FOUND for {symbol} on {date}")
        raise HTTPException(status_code=404, detail="Price not found or date invalid")
    return {"symbol": symbol.upper(), "date": date, "price": price}

@app.get("/simulate")
def simulate(
    amount: float,
    symbol: str,
    buy: str,
    sell: str
):
    result = simulate_invest(amount, symbol.upper(), buy, sell)

    if result is None:
        raise HTTPException(status_code=400, detail="Invalid symbol or data unavailable for dates")

    return {
        "amount": amount,
        "symbol": symbol.upper(),
        "buy": buy,
        "sell": sell,
        "future_value": result
    }

# --- Portfolio Routes ---

@app.post("/users")
def create_user(req: CreateUserRequest):
    user_id = portfolio.create_user(req.username)
    if not user_id:
        raise HTTPException(status_code=400, detail="User already exists or error creating user")
    return {"user_id": user_id, "username": req.username}

@app.post("/portfolio/create")
def create_portfolio(req: CreatePortfolioRequest):
    result = portfolio.create_portfolio(req.user_id, req.name, req.currency_code)
    if not result:
        raise HTTPException(status_code=400, detail="Error creating portfolio (name might be taken for this user)")
    return result

def _resolve_trade_date(portfolio_id: int, requested_date: Optional[str]):
    """
    Helper to determine the valid trade date.
    - If session active: Returns session date.
    - If no session: Returns requested_date (must be provided).
    """
    session = game_engine.get_session(portfolio_id)
    if session:
        return session["sim_date"]
    
    if not requested_date:
        raise HTTPException(status_code=400, detail="Date required (no active session)")
    
    return requested_date

@app.post("/portfolio/buy")
def buy_asset(req: TradeRequest):
    trade_date = _resolve_trade_date(req.portfolio_id, req.date)
    
    result = portfolio.add_transaction(req.portfolio_id, req.symbol.upper(), "BUY", req.quantity, trade_date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/portfolio/sell")
def sell_asset(req: TradeRequest):
    trade_date = _resolve_trade_date(req.portfolio_id, req.date)
    
    result = portfolio.add_transaction(req.portfolio_id, req.symbol.upper(), "SELL", req.quantity, trade_date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/portfolio/{portfolio_id}/value")
def get_portfolio_value(portfolio_id: int, date: Optional[str] = None):
    # If date is missing, try to use session date, else fail
    if not date:
        session = game_engine.get_session(portfolio_id)
        if session:
            date = session["sim_date"]
        else:
            raise HTTPException(status_code=400, detail="Date required (no active session)")

    result = portfolio.get_portfolio_value(portfolio_id, date)
    if not result:
        raise HTTPException(status_code=404, detail="Portfolio not found or error calculating value")
    return result

@app.get("/portfolio/{portfolio_id}")
def get_portfolio_details(portfolio_id: int):
    p = portfolio.get_portfolio(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    h = portfolio.get_holdings(portfolio_id)
    
    # Enrich with session data if exists
    session = game_engine.get_session(portfolio_id)
    
    return {**p, "holdings": h, "active_session": session}

# --- Simulation / Game Routes ---

@app.post("/simulation/start")
def start_simulation(req: StartSimRequest):
    print(f"DEBUG: Starting simulation for User {req.user_id}, Portfolio {req.portfolio_id}")
    print(f"DEBUG: Start Date: {req.start_date}, Salary: {req.monthly_salary}")
    
    result = game_engine.create_session(
        req.user_id, 
        req.portfolio_id, 
        req.start_date, 
        req.monthly_salary, 
        req.monthly_expenses
    )
    
    if "error" in result:
        print(f"DEBUG: Simulation start failed: {result['error']}")
        raise HTTPException(status_code=400, detail=result["error"])
        
    print(f"DEBUG: Simulation started successfully: {result}")
    return result

@app.post("/simulation/forward")
def advance_simulation(req: ForwardSimRequest):
    result = game_engine.advance_time(req.portfolio_id, req.target_date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/simulation/status")
def get_simulation_status(portfolio_id: int):
    session = game_engine.get_session(portfolio_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active session for this portfolio")
    
    # Get Portfolio Value at current sim date
    val = portfolio.get_portfolio_value(portfolio_id, session["sim_date"])
    if not val:
        raise HTTPException(status_code=500, detail="Error calculating value")
        
    return {
        "session": session,
        "portfolio_value": val
    }

@app.get("/simulation/list")
def list_user_sessions(user_id: int):
    sessions = game_engine.list_sessions(user_id)
    return {"user_id": user_id, "sessions": sessions}

@app.get("/currencies")
def get_currencies():
    return db_currency.get_all_rates()

@app.post("/reset")
def reset_system():
    try:
        with get_db_connection() as conn:
            try:
                cur = conn.cursor()
                
                # Drop all user-related tables
                cur.execute("DROP TABLE IF EXISTS game_sessions, transactions, portfolios, users CASCADE;")
                
                # Re-initialize schema
                schema_path = os.path.join(os.path.dirname(__file__), "portfolio_schema.sql")
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                    cur.execute(schema_sql)
                    
                conn.commit()
                return {"status": "success", "message": "System reset successfully"}
            except Exception as e:
                conn.rollback()
                raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")
