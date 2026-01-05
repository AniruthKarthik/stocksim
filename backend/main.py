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

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (rest of imports and models)

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