import psycopg2
from .db_prices import connect, get_asset_id, get_price
from .db_currency import get_rate
from datetime import datetime

def create_user(username: str):
    conn = connect()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError:
        conn.rollback()
        return None # User already exists
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return None
    finally:
        conn.close()

def create_portfolio(user_id: int, name: str, currency_code: str = "USD"):
    conn = connect()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO portfolios (user_id, name, currency_code) 
            VALUES (%s, %s, %s) 
            RETURNING id, cash_balance, currency_code
        """, (user_id, name, currency_code))
        row = cur.fetchone()
        conn.commit()
        return {"id": row[0], "cash_balance": float(row[1]), "currency_code": row[2]}
    except Exception as e:
        conn.rollback()
        print(f"Error creating portfolio: {e}")
        return None
    finally:
        conn.close()

def get_portfolio(portfolio_id: int):
    conn = connect()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, name, cash_balance, currency_code FROM portfolios WHERE id = %s", (portfolio_id,))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "user_id": row[1], "name": row[2], "cash_balance": float(row[3]), "currency_code": row[4]}
        return None
    finally:
        conn.close()

def get_holdings(portfolio_id: int):
    """
    Calculate current holdings based on transaction history.
    Returns a dict: { "AAPL": 10.5, "MSFT": 5.0 }
    """
    conn = connect()
    if not conn: return {}
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, type, quantity 
            FROM transactions 
            WHERE portfolio_id = %s
        """, (portfolio_id,))
        
        holdings = {}
        for symbol, txn_type, qty in cur.fetchall():
            qty = float(qty)
            if symbol not in holdings:
                holdings[symbol] = 0.0
            
            if txn_type == "BUY":
                holdings[symbol] += qty
            elif txn_type == "SELL":
                holdings[symbol] -= qty
        
        # Remove zero or negative holdings (shouldn't happen if logic is correct)
        return {k: v for k, v in holdings.items() if v > 0}
    finally:
        conn.close()

def add_transaction(portfolio_id: int, symbol: str, txn_type: str, quantity: float, date: str):
    """
    Executes a transaction:
    1. Validates price availability.
    2. Checks funds (for BUY) or holdings (for SELL).
    3. Updates cash balance.
    4. Records transaction.
    """
    asset_id = get_asset_id(symbol)
    if not asset_id:
        return {"error": f"Asset {symbol} not found"}

    price = get_price(symbol, date)
    if price is None:
        return {"error": f"Price not available for {symbol} on {date}"}

    total_cost = price * quantity
    
    conn = connect()
    if not conn: return {"error": "DB Connection failed"}
    
    try:
        cur = conn.cursor()
        
        # Check Portfolio Balance / Holdings
        cur.execute("SELECT cash_balance, currency_code FROM portfolios WHERE id = %s FOR UPDATE", (portfolio_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Portfolio not found"}
        
        cash_balance = float(row[0])
        currency_code = row[1]
        
        # Convert total_cost (USD) to portfolio currency
        rate = get_rate(currency_code)
        cost_in_port_currency = total_cost * rate
        
        if txn_type == "BUY":
            if cash_balance < cost_in_port_currency:
                return {"error": f"Insufficient funds. Required: {cost_in_port_currency} {currency_code}, Available: {cash_balance} {currency_code}"}
            new_balance = cash_balance - cost_in_port_currency
        
        elif txn_type == "SELL":
            # We need to verify holdings outside the transaction block or calculate it here
            # For simplicity, we assume the caller or a prior check validated holdings, 
            # BUT strict ACID requires checking inside transaction.
            # Let's quickly re-sum holdings for this asset inside the txn for safety.
            cur.execute("""
                SELECT type, quantity FROM transactions 
                WHERE portfolio_id = %s AND symbol = %s
            """, (portfolio_id, symbol))
            current_qty = 0.0
            for t_type, t_qty in cur.fetchall():
                if t_type == "BUY": current_qty += float(t_qty)
                else: current_qty -= float(t_qty)
            
            if current_qty < quantity:
                return {"error": f"Insufficient holdings. Owned: {current_qty}, Selling: {quantity}"}
                
            new_balance = cash_balance + cost_in_port_currency
        else:
            return {"error": "Invalid transaction type"}

        # Update Balance
        cur.execute("UPDATE portfolios SET cash_balance = %s WHERE id = %s", (new_balance, portfolio_id))

        # Record Transaction
        cur.execute("""
            INSERT INTO transactions (portfolio_id, asset_id, type, symbol, quantity, price_per_unit, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (portfolio_id, asset_id, txn_type, symbol, quantity, price, date))

        conn.commit()
        return {
            "status": "success", 
            "type": txn_type, 
            "symbol": symbol, 
            "quantity": quantity, 
            "price": price, 
            "total": total_cost,
            "new_balance": new_balance
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

def get_portfolio_value(portfolio_id: int, date: str):
    """
    Computes total portfolio value (Cash + Asset Value) on a specific date.
    """
    port = get_portfolio(portfolio_id)
    if not port: return None

    # Get holdings up to that date? 
    # Current requirement says "get portfolio value for any date".
    # This implies we need to reconstruct holdings at that date.
    # For simplicity, let's calculate value of CURRENT holdings at THAT date's price.
    # OR, better: Replay transactions up to `date` to get holdings on that date.
    
    # Let's do the robust way: Replay transactions <= date
    conn = connect()
    holdings = {}
    cash_at_date = 10000.00 # Assuming start. But we store current balance.
    # Actually, tracking cash history is hard without a ledger. 
    # Simplification: Use *current* holdings and value them at `date` price? 
    # No, that's wrong for backtesting.
    # Correct way: Sum transactions <= date.
    
    # We will assume initial cash is 10000 (as per schema default) and reconstruct cash flow.
    # This is getting complex.
    # Let's stick to: Value of CURRENT holdings at DATE price + CURRENT cash. 
    # Use Case: "How much is my portfolio worth today?" or "How much was it worth yesterday?"
    # If the user asks for historical value, using current holdings is technically wrong if they traded in between.
    # However, for a simple simulator, maybe "Value of holdings as of Date X" is what's meant.
    
    # Let's try to do it right:
    # 1. Get all transactions <= date
    # 2. Compute holdings and cash balance resulting from those transactions.
    
    try:
        cur = conn.cursor()
        
        # 1. Get Actual Current Cash Balance from DB (Source of Truth)
        # We prefer this over reconstructing from transactions because transactions don't track salary.
        # Limitation: If 'date' is in the past, this still returns CURRENT cash. 
        # But for the Dashboard (current state), this is exactly what we want.
        cur.execute("SELECT cash_balance, currency_code FROM portfolios WHERE id = %s", (portfolio_id,))
        row = cur.fetchone()
        if not row: return None
        
        raw_cash = float(row[0])
        currency_code = row[1]
        
        # Convert cash to USD for total valuation
        rate = get_rate(currency_code)
        real_cash_balance_usd = raw_cash / rate

        cur.execute("""
            SELECT type, quantity, price_per_unit, symbol 
            FROM transactions 
            WHERE portfolio_id = %s AND date <= %s
            ORDER BY date ASC, id ASC
        """, (portfolio_id, date))
        
        hist_holdings = {} # sym -> qty
        cost_basis = {}    # sym -> total_invested
        
        for t_type, qty, price, sym in cur.fetchall():
            qty = float(qty)
            price = float(price)
            val = qty * price
            
            if sym not in hist_holdings: 
                hist_holdings[sym] = 0.0
                cost_basis[sym] = 0.0
            
            if t_type == "BUY":
                hist_holdings[sym] += qty
                cost_basis[sym] += val
            elif t_type == "SELL":
                # Reduce cost basis proportionally
                current_qty = hist_holdings[sym]
                if current_qty > 0:
                    avg_cost = cost_basis[sym] / current_qty
                    cost_basis[sym] -= (avg_cost * qty)
                    hist_holdings[sym] -= qty
                else:
                    # Should not happen if data is consistent
                    pass

        # Now value these holdings at `date` price
        total_assets_value = 0.0
        total_invested_value = 0.0
        missing_prices = []
        detailed_holdings = []
        
        for sym, qty in hist_holdings.items():
            if qty > 0:
                invested = cost_basis.get(sym, 0.0)
                total_invested_value += invested
                
                p = get_price(sym, date)
                if p:
                    val = qty * p
                    total_assets_value += val
                    detailed_holdings.append({
                        "symbol": sym,
                        "quantity": qty,
                        "price": p,
                        "value": val,
                        "invested": invested,
                        "pnl": val - invested,
                        "pnl_percent": ((val - invested) / invested * 100) if invested > 0 else 0
                    })
                else:
                    missing_prices.append(sym)
                    detailed_holdings.append({
                        "symbol": sym,
                        "quantity": qty,
                        "price": 0.0,
                        "value": 0.0,
                        "invested": invested,
                        "pnl": -invested, # Lost everything if price is 0? Or just unknown.
                        "pnl_percent": -100.0
                    })
        
        return {
            "date": date,
            "cash": real_cash_balance_usd,
            "assets_value": total_assets_value,
            "invested_value": total_invested_value,
            "total_value": real_cash_balance_usd + total_assets_value,
            "holdings": detailed_holdings,
            "missing_prices": missing_prices
        }
        
    except Exception as e:
        print(e)
        return None
    finally:
        conn.close()
