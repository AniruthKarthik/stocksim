import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db_conn import get_db_connection

def optimize():
    print("🚀 Starting Database Optimization...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Index for Price lookups (Used in almost every simulation step)
                print("  Creating index on prices(asset_id, date DESC)...")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_asset_date ON prices(asset_id, date DESC);")
                
                # 2. Index for Transaction history (Speeds up portfolio value calculation)
                print("  Creating index on transactions(portfolio_id)...")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_id ON transactions(portfolio_id);")
                
                # 3. Index for Game Sessions (Speeds up status checks)
                print("  Creating index on game_sessions(portfolio_id, is_active)...")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_port_active ON game_sessions(portfolio_id, is_active);")
                
                # 4. Index for Asset Symbol lookups
                print("  Creating index on assets(symbol)...")
                # Symbol is already UNIQUE, so it has an index, but we ensure it.
                
                conn.commit()
                print("✅ Database optimized successfully!")
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

if __name__ == "__main__":
    optimize()
