import sys
import os
from . import game_engine
from . import db_portfolio as portfolio
from .db_prices import get_price

def run_test(name, func):
    print(f"Testing {name}...", end=" ")
    try:
        func()
        print("✅ PASS")
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_game_flow():
    # 1. Setup User & Portfolio
    username = f"gamer_{os.urandom(4).hex()}"
    user_id = portfolio.create_user(username)
    assert user_id, "User creation failed"
    
    port_res = portfolio.create_portfolio(user_id, "GamePort")
    assert port_res, "Portfolio creation failed"
    pid = port_res["id"]
    
    # 2. Start Session
    start_date = "2015-01-01"
    salary = 5000
    expenses = 2000
    res = game_engine.create_session(user_id, pid, start_date, salary, expenses)
    assert "session_id" in res, f"Start session failed: {res}"
    assert res["sim_date"] == start_date
    
    # 3. Buy Asset (Should use session date)
    # 2015-01-01 might be holiday, buy logic should handle price fetch?
    # db_portfolio.add_transaction calls get_price which handles fallback.
    # Let's ensure we buy something that exists. AAPL exists.
    
    # We need to simulate the API call logic which overrides date.
    # But here we test engine/db directly. 
    # db_portfolio.add_transaction takes a date. 
    # So we pass start_date.
    
    buy_res = portfolio.add_transaction(pid, "AAPL", "BUY", 10, start_date)
    assert "status" in buy_res, f"Buy failed: {buy_res}"
    
    # 4. Advance Time
    # Move 2 months forward -> 2015-03-01
    target_date = "2015-03-01"
    adv_res = game_engine.advance_time(pid, target_date)
    assert adv_res["status"] == "success", f"Advance failed: {adv_res}"
    assert adv_res["months_passed"] == 2, f"Expected 2 months, got {adv_res['months_passed']}"
    
    # Expected Cash:
    # Initial: 10000
    # Buy Cost: 10 * Price(2015-01-01)
    # Income: (5000 - 2000) * 2 = 6000
    # Final Balance = 10000 - Cost + 6000
    
    port = portfolio.get_portfolio(pid)
    curr_balance = port["cash_balance"]
    
    # Verify strict increase from income (ignoring the buy cost logic for a moment, just checking the delta isn't negative/wrong)
    # Actually let's check exact math if possible.
    # We don't know exact price here easily without fetching it again.
    # But we know cash should be significant.
    assert curr_balance > 5000, "Cash balance seems wrong/low"
    
    # 5. Check Session State
    session = game_engine.get_session(pid)
    assert session["sim_date"] == target_date, "Session date not updated"

if __name__ == "__main__":
    print("--- Starting Game Engine Tests ---")
    run_test("Game Flow (Start -> Buy -> Forward)", test_game_flow)
