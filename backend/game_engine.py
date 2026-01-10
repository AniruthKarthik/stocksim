from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from .db_conn import get_db_connection

from .db_currency import get_rate

def create_session(user_id: int, portfolio_id: int, start_date: str, monthly_salary: float = 0, monthly_expenses: float = 0, initial_cash: float = 0, currency_code: str = "USD"):
    """
    Starts a new game session.
    Automatically deactivates any existing active session for this portfolio.
    """
    # Convert incoming amounts (in user's currency) to USD for storage
    rate = get_rate(currency_code)
    usd_cash = initial_cash / rate
    usd_salary = monthly_salary / rate
    usd_expenses = monthly_expenses / rate

    # Debug logging to a file we can definitely check
    with open("simulation_debug.log", "a") as f:
        f.write(f"[{datetime.now()}] START SIM: user={user_id} port={portfolio_id} start={start_date} salary={monthly_salary} ({usd_salary} USD) cash={initial_cash} ({usd_cash} USD) rate={rate} ({currency_code})\n")
    
    print(f"DEBUG: Initializing session. User: {user_id}, Port: {portfolio_id}, Start: {start_date}, Init Cash: {usd_cash} USD (from {initial_cash} {currency_code})")
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Deactivate active sessions for this portfolio
            cur.execute("""
                UPDATE game_sessions 
                SET is_active = FALSE 
                WHERE portfolio_id = %s AND is_active = TRUE
            """, (portfolio_id,))

            # Validate start_date format
            try:
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Invalid date format. Use YYYY-MM-DD"}

            # Create session
            cur.execute("""
                INSERT INTO game_sessions 
                (user_id, portfolio_id, start_date, sim_date, monthly_salary, monthly_expenses, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (user_id, portfolio_id, s_date, s_date, usd_salary, usd_expenses))
            
            row = cur.fetchone()
            if not row:
                return {"error": "Failed to create session row"}
            session_id = row[0]
            
            # Initialize portfolio cash to the specified initial_cash (now in USD)
            print(f"DEBUG: Updating portfolio {portfolio_id} balance to {usd_cash}")
            cur.execute("UPDATE portfolios SET cash_balance = %s WHERE id = %s", (usd_cash, portfolio_id))

            conn.commit()
            return {"session_id": session_id, "start_date": start_date, "sim_date": start_date}

    except Exception as e:
        print(f"DEBUG: create_session CRITICAL ERROR: {e}")
        return {"error": str(e)}

def get_session(portfolio_id: int):
    """
    Returns the active session for a portfolio.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, start_date, sim_date, monthly_salary, monthly_expenses 
                FROM game_sessions 
                WHERE portfolio_id = %s AND is_active = TRUE
            """, (portfolio_id,))
            row = cur.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "start_date": str(row[1]),
                    "sim_date": str(row[2]),
                    "monthly_salary": float(row[3]),
                    "monthly_expenses": float(row[4])
                }
            return None
    except Exception:
        return None

def list_sessions(user_id: int):
    """
    Returns all sessions for a user (history).
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, portfolio_id, start_date, sim_date, is_active, created_at
                FROM game_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            
            sessions = []
            for row in cur.fetchall():
                sessions.append({
                    "id": row[0],
                    "portfolio_id": row[1],
                    "start_date": str(row[2]),
                    "sim_date": str(row[3]),
                    "is_active": row[4],
                    "created_at": str(row[5])
                })
            return sessions
    except Exception:
        return []

def update_monthly_investment(portfolio_id: int, new_amount: float):
    """
    Updates the monthly salary/investment for the active session of a portfolio.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE game_sessions
                SET monthly_salary = %s
                WHERE portfolio_id = %s AND is_active = TRUE
            """, (new_amount, portfolio_id))
            conn.commit()
            return {"status": "success", "new_amount": new_amount}
    except Exception as e:
        return {"error": str(e)}

def advance_time(portfolio_id: int, target_date: str):
    """
    Moves the simulation forward to target_date.
    Calculates salary/expenses for crossed months.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Lock session row
            cur.execute("""
                SELECT s.id, s.sim_date, s.monthly_salary, s.monthly_expenses, p.currency_code 
                FROM game_sessions s
                JOIN portfolios p ON s.portfolio_id = p.id
                WHERE s.portfolio_id = %s AND s.is_active = TRUE
                FOR UPDATE
            """, (portfolio_id,))
            row = cur.fetchone()
            if not row:
                return {"error": "No active session found"}
            
            session_id, current_sim_date, salary, expenses, currency_code = row
            current_sim_date_obj = current_sim_date # it's already a date object from psycopg2
            
            # Parse target date
            try:
                target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Invalid date format"}
                
            # Validation: Cannot go back
            if target_date_obj <= current_sim_date_obj:
                return {"error": f"Cannot time travel backwards or stay same. Current: {current_sim_date}, Target: {target_date}"}
                
            # Calculate months passed
            # Simple logic: (YearDiff * 12) + MonthDiff
            # Example: Jan 15 -> Feb 14. (2-1) = 1 month.
            months_passed = (target_date_obj.year - current_sim_date_obj.year) * 12 + (target_date_obj.month - current_sim_date_obj.month)
            
            # Avoid negative months logic (though date check covers it)
            months_passed = max(0, months_passed)
            
            net_monthly = float(salary) - float(expenses)
            total_cash_change = net_monthly * months_passed
            
            # Update Portfolio Cash
            if total_cash_change != 0:
                cur.execute("""
                    UPDATE portfolios 
                    SET cash_balance = cash_balance + %s 
                    WHERE id = %s
                """, (total_cash_change, portfolio_id))
                
            # Update Session Date
            cur.execute("""
                UPDATE game_sessions 
                SET sim_date = %s 
                WHERE id = %s
            """, (target_date_obj, session_id))
            
            conn.commit()
            
            return {
                "status": "success",
                "previous_date": str(current_sim_date_obj),
                "new_date": str(target_date_obj),
                "months_passed": months_passed,
                "cash_added": total_cash_change
            }
            
    except Exception as e:
        return {"error": str(e)}