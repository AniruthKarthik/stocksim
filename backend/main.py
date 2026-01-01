from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .simulator import simulate_invest
from .db_prices import get_price
from . import db_portfolio as portfolio

app = FastAPI()

# --- Pydantic Models ---
class CreateUserRequest(BaseModel):
    username: str

class CreatePortfolioRequest(BaseModel):
    user_id: int
    name: str

class TradeRequest(BaseModel):
    portfolio_id: int
    symbol: str
    quantity: float
    date: str # YYYY-MM-DD

class ValueRequest(BaseModel):
    portfolio_id: int
    date: str

# --- Routes ---

@app.get("/")
def home():
    return {"status": "ok", "message": "StockSim Backend API"}

@app.get("/price")
def get_asset_price(symbol: str, date: str):
    price = get_price(symbol.upper(), date)
    if price is None:
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
    result = portfolio.create_portfolio(req.user_id, req.name)
    if not result:
        raise HTTPException(status_code=400, detail="Error creating portfolio (name might be taken for this user)")
    return result

@app.post("/portfolio/buy")
def buy_asset(req: TradeRequest):
    result = portfolio.add_transaction(req.portfolio_id, req.symbol.upper(), "BUY", req.quantity, req.date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/portfolio/sell")
def sell_asset(req: TradeRequest):
    result = portfolio.add_transaction(req.portfolio_id, req.symbol.upper(), "SELL", req.quantity, req.date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/portfolio/{portfolio_id}/value")
def get_portfolio_value(portfolio_id: int, date: str):
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
    return {**p, "holdings": h}