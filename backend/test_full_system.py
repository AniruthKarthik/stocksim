import sys
import os

from .db_prices import get_price
from .simulator import simulate_invest
from . import db_portfolio as portfolio
from datetime import datetime

def run_test(name, func):
    print(f"Testing {name}...", end=" ")
    try:
        func()
        print("✅ PASS")
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_price_fetch():
    # Test known date
    p = get_price("APPLE", "2023-01-03")
    assert p is not None, "Should find price for APPLE on 2023-01-03"
    assert isinstance(p, float), "Price should be float"
    
    # Test weekend fallback (Jan 1 2023 was Sunday)
    # The loader loaded data. Check if 2023 data exists.
    # If Jan 3 is valid, Jan 1 might be missing.
    # The fallback logic should find Jan 3 or Jan 4.
    p_fallback = get_price("APPLE", "2023-01-01")
    assert p_fallback is not None, "Should fallback for missing date"
    assert p_fallback == p, f"Fallback should match next trading day price. Got {p_fallback}, expected {p}"

def test_simulator():
    # Buy 100$ worth.
    # If logic is: units = amount / buy_price; value = units * sell_price
    # value = (amount / buy_price) * sell_price
    res = simulate_invest(100.0, "APPLE", "2023-01-01", "2023-01-05")
    assert res is not None, "Simulation should return result"
    assert res > 0, "Future value should be positive"

def test_portfolio_lifecycle():
    # 1. Create User
    username = f"test_user_{int(datetime.now().timestamp())}"
    user_id = portfolio.create_user(username)
    assert user_id is not None, "Failed to create user"

    # 2. Create Portfolio
    port_data = portfolio.create_portfolio(user_id, "Retirement")
    assert port_data is not None, "Failed to create portfolio"
    pid = port_data["id"]
    initial_cash = port_data["cash_balance"]
    assert initial_cash == 10000.0, "Initial balance should be 10000"

    # 3. Buy Asset (APPLE)
    # Let's buy on a date we know has price. 2023-01-03.
    # Price is approx $125 (split adjusted? checking data...)
    # We will trust the DB.
    buy_date = "2023-01-03"
    price = get_price("APPLE", buy_date)
    assert price is not None, "Price check failed"
    
    qty = 10
    cost = qty * price
    
    res = portfolio.add_transaction(pid, "APPLE", "BUY", qty, buy_date)
    assert "error" not in res, f"Buy failed: {res.get('error')}"
    assert res["new_balance"] == initial_cash - cost, "Balance update incorrect"

    # 4. Check Holdings
    holdings = portfolio.get_holdings(pid)
    assert holdings["APPLE"] == 10.0, f"Holdings mismatch. Expected 10.0, got {holdings.get('APPLE')}"

    # 5. Sell Partial
    sell_date = "2023-01-05"
    sell_qty = 4
    sell_price = get_price("APPLE", sell_date)
    
    res = portfolio.add_transaction(pid, "APPLE", "SELL", sell_qty, sell_date)
    assert "error" not in res, f"Sell failed: {res.get('error')}"
    
    # 6. Verify Final State
    holdings = portfolio.get_holdings(pid)
    assert holdings["APPLE"] == 6.0, f"Holdings mismatch after sell. Expected 6.0, got {holdings.get('APPLE')}"
    
    final_balance = initial_cash - cost + (sell_qty * sell_price)
    port_info = portfolio.get_portfolio(pid)
    # Float comparison with tolerance
    assert abs(port_info["cash_balance"] - final_balance) < 0.01, f"Final balance mismatch. DB: {port_info['cash_balance']}, Calc: {final_balance}"

    # 7. Portfolio Value
    # Value on sell_date should be: Cash Balance + (6.0 * Price on sell_date)
    val_data = portfolio.get_portfolio_value(pid, sell_date)
    expected_asset_val = 6.0 * sell_price
    assert abs(val_data["assets_value"] - expected_asset_val) < 0.01, "Asset value calculation incorrect"
    assert abs(val_data["total_value"] - (final_balance + expected_asset_val)) < 0.01, "Total value calculation incorrect"


if __name__ == "__main__":
    print("--- Starting Backend Tests ---")
    run_test("Price Fetching & Fallback", test_price_fetch)
    run_test("Investment Simulator", test_simulator)
    run_test("Portfolio System (User -> Create -> Buy -> Sell -> Value)", test_portfolio_lifecycle)
    print("--- Tests Complete ---")
