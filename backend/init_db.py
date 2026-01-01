import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = dict(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost")
)

def run_sql_file(cursor, filename):
    print(f"Running {filename}...")
    with open(filename, 'r') as f:
        sql = f.read()
        cursor.execute(sql)

def init():
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        
        # We assume stocksim_schema might fail if tables exist, but let's try.
        # Actually, standard pg_dump includes CREATE TABLE which might fail if exists.
        # But the portfolio schema has IF NOT EXISTS.
        # Let's just run portfolio_schema.sql since the user said stocksim_schema.sql is "existing".
        # If I run stocksim_schema.sql again it might error out.
        # I'll only run portfolio_schema.sql for now as that's the delta.
        
        run_sql_file(cur, "backend/portfolio_schema.sql")
        
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init()
