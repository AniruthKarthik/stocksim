import psycopg2
from .db_prices import get_asset_id, get_price
from .db_conn import get_db_connection
from .db_currency import get_rate
from datetime import datetime

def create_user(username: str):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    except psycopg2.IntegrityError:
        raise ValueError("User already exists")
    except Exception as e:
        print(f"Error creating user: {e}")
        raise e

def create_portfolio(user_id: int, name: str, currency_code: str = "USD"):
    try:
        with get_db_connection() as conn:
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
        print(f"Error creating portfolio: {e}")
        return None

def get_portfolio(portfolio_id: int):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, user_id, name, cash_balance, currency_code FROM portfolios WHERE id = %s", (portfolio_id,))
            row = cur.fetchone()
            if row:
                return {"id": row[0], "user_id": row[1], "name": row[2], "cash_balance": float(row[3]), "currency_code": row[4]}
            return None
    except Exception:
        return None

def get_holdings(portfolio_id: int):
    """
    Calculate current holdings based on transaction history.
    Returns a dict: { "AAPL": 10.5, "MSFT": 5.0 }
    """
    try:
        with get_db_connection() as conn:
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
    except Exception:
        return {}

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
    
    try:
        with get_db_connection() as conn:
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
        return {"error": str(e)}

def get_portfolio_value(portfolio_id: int, date: str):
    """
    Computes total portfolio value (Cash + Asset Value) on a specific date.
    Optimized to use asset_ids and avoid redundant joins.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # 1. Get Actual Current Cash Balance
            cur.execute("SELECT cash_balance, currency_code FROM portfolios WHERE id = %s", (portfolio_id,))
            row = cur.fetchone()
            if not row: return None
            
            raw_cash = float(row[0])
            currency_code = row[1]
            
            # Convert cash to USD for total valuation
            rate = get_rate(currency_code)
            real_cash_balance_usd = raw_cash / rate

            # 2. Get Transactions with asset_id
            cur.execute("""
                SELECT type, quantity, price_per_unit, symbol, asset_id
                FROM transactions 
                WHERE portfolio_id = %s AND date <= %s
                ORDER BY date ASC, id ASC
            """, (portfolio_id, date))
            
            hist_holdings = {} # asset_id -> qty
            symbol_map = {}    # asset_id -> symbol
            cost_basis = {}    # asset_id -> total_invested
            
            for t_type, qty, price, sym, aid in cur.fetchall():
                qty = float(qty)
                price = float(price)
                val = qty * price
                
                if aid not in hist_holdings: 
                    hist_holdings[aid] = 0.0
                    cost_basis[aid] = 0.0
                    symbol_map[aid] = sym
                
                if t_type == "BUY":
                    hist_holdings[aid] += qty
                    cost_basis[aid] += val
                elif t_type == "SELL":
                    current_qty = hist_holdings[aid]
                    if current_qty > 0:
                        avg_cost = cost_basis[aid] / current_qty
                        cost_basis[aid] -= (avg_cost * qty)
                        hist_holdings[aid] -= qty

            # 3. Batch fetch prices for held assets
            held_asset_ids = [aid for aid, qty in hist_holdings.items() if qty > 0]
            price_map = {}
            
            if held_asset_ids:
                # Optimized: Use LATERAL JOIN to efficiently find the latest price for each asset.
                # This forces the query planner to use the (asset_id, date) index for each ID 
                # instead of scanning a large range of dates for IN (...).
                query = """
                    SELECT t.asset_id, p.adj_close
                    FROM unnest(%s::int[]) as t(asset_id)
                    CROSS JOIN LATERAL (
                        SELECT adj_close
                        FROM prices
                        WHERE asset_id = t.asset_id AND date <= %s
                        ORDER BY date DESC
                        LIMIT 1
                    ) p
                """
                cur.execute(query, (held_asset_ids, date))
                
                for row in cur.fetchall():
                    price_map[row[0]] = float(row[1])

            # 4. Calculate final values
            total_assets_value = 0.0
            total_invested_value = 0.0
            missing_prices = []
            detailed_holdings = []
            
            for aid, qty in hist_holdings.items():
                if qty > 0:
                    sym = symbol_map[aid]
                    invested = cost_basis.get(aid, 0.0)
                    total_invested_value += invested
                    
                    p = price_map.get(aid)
                    
                    # Fallback: If bulk query missed (unlikely if logic matches), try individual
                    if p is None:
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
                            "pnl": -invested,
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
        print(f"Error in get_portfolio_value: {e}")
        return None
