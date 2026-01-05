
import psycopg2
import os
import random
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost")
}

def seed():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Insert Assets
        assets = [
            ("AAPL", "Apple Inc.", "stocks", 5.0), # Start price in 2000
            ("BTC-USD", "Bitcoin USD", "crypto", 100.0), # Start price (late)
            ("MSFT", "Microsoft Corp.", "stocks", 40.0), 
            ("TSLA", "Tesla Inc.", "stocks", 15.0)
        ]
        
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()
        days_delta = (end_date - start_date).days
        
        for sym, name, type_, start_price in assets:
            cur.execute(
                "INSERT INTO assets (symbol, name, type) VALUES (%s, %s, %s) ON CONFLICT (symbol) DO NOTHING RETURNING id",
                (sym, name, type_)
            )
            res = cur.fetchone()
            if not res:
                cur.execute("SELECT id FROM assets WHERE symbol = %s", (sym,))
                asset_id = cur.fetchone()[0]
            else:
                asset_id = res[0]
            
            print(f"Generating history for {sym}...")
            
            # Generate history
            current_price = start_price
            values = []
            
            # For crypto, use all days. For stocks, skip weekends approx.
            # Simple simulation: just do every day for robustness in this seed
            
            for i in range(days_delta + 1):
                d = start_date + timedelta(days=i)
                
                # Simple Random Walk
                change = random.uniform(-0.02, 0.02) # +/- 2%
                current_price = current_price * (1 + change)
                if current_price < 0.01: current_price = 0.01
                
                # BTC didn't exist in 2000, but for simulation simplicity we fill it 
                # OR we can just fill it with dummy low values until 2010
                if sym == 'BTC-USD' and d.year < 2010:
                     price = 0.01
                else:
                     price = current_price
                
                values.append((asset_id, d.strftime('%Y-%m-%d'), price, price, 1000000))
                
                if len(values) >= 5000:
                    execute_values(cur, 
                        "INSERT INTO prices (asset_id, date, close, adj_close, volume) VALUES %s ON CONFLICT (asset_id, date) DO NOTHING",
                        values
                    )
                    values = []
            
            if values:
                execute_values(cur, 
                    "INSERT INTO prices (asset_id, date, close, adj_close, volume) VALUES %s ON CONFLICT (asset_id, date) DO NOTHING",
                    values
                )
            
        conn.commit()
        print("Seeded comprehensive history successfully.")
    except Exception as e:
        print(f"Seed failed: {e}")

if __name__ == "__main__":
    seed()
