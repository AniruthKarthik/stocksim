import psycopg2
from .db_prices import connect, get_asset_id, get_price
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

def create_portfolio(user_id: int, name: str):
    conn = connect()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO portfolios (user_id, name) 
            VALUES (%s, %s) 
            RETURNING id, cash_balance
        """, (user_id, name))
        row = cur.fetchone()
        conn.commit()
        return {"id": row[0], "cash_balance": float(row[1])}
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
        cur.execute("SELECT id, user_id, name, cash_balance FROM portfolios WHERE id = %s", (portfolio_id,))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "user_id": row[1], "name": row[2], "cash_balance": float(row[3])}
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
        cur.execute("SELECT cash_balance FROM portfolios WHERE id = %s FOR UPDATE", (portfolio_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Portfolio not found"}
        
        cash_balance = float(row[0])
        
        if txn_type == "BUY":
            if cash_balance < total_cost:
                return {"error": f"Insufficient funds. Required: {total_cost}, Available: {cash_balance}"}
            new_balance = cash_balance - total_cost
        
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
                
            new_balance = cash_balance + total_cost
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
        cur.execute("""
            SELECT type, quantity, price_per_unit, symbol 
            FROM transactions 
            WHERE portfolio_id = %s AND date <= %s
        """, (portfolio_id, date))
        
        hist_holdings = {}
        hist_cash = 10000.00 # Default start
        
        for t_type, qty, price, sym in cur.fetchall():
            qty = float(qty)
            price = float(price)
            val = qty * price
            
            if sym not in hist_holdings: hist_holdings[sym] = 0.0
            
            if t_type == "BUY":
                hist_cash -= val
                hist_holdings[sym] += qty
            elif t_type == "SELL":
                hist_cash += val
                hist_holdings[sym] -= qty
        
        # Now value these holdings at `date` price
        total_assets_value = 0.0
        missing_prices = []
        
        for sym, qty in hist_holdings.items():
            if qty > 0:
                p = get_price(sym, date)
                if p:
                    total_assets_value += qty * p
                else:
                    missing_prices.append(sym)
        
        return {
            "date": date,
            "cash": round(hist_cash, 2),
            "assets_value": round(total_assets_value, 2),
            "total_value": round(hist_cash + total_assets_value, 2),
            "holdings": {k: v for k, v in hist_holdings.items() if v > 0},
            "missing_prices": missing_prices
        }
        
    except Exception as e:
        print(e)
        return None
    finally:
        conn.close()
