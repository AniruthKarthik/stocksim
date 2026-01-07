import os
import psycopg2
from dotenv import load_dotenv
import sys

# Add parent directory to path to import backend modules if needed, 
# but we are just running raw SQL here.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

# Verify environment variables are loaded
if os.getenv("DATABASE_URL"):
    # If we have the full URL, we are good.
    pass
else:
    required_vars = ["DB_HOST", "DB_USER", "DB_NAME", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease ensure you have a .env file in the project root with these variables set.")
        print("OR set a single DATABASE_URL variable.")
        sys.exit(1)

if os.getenv("DATABASE_URL"):
    DB_CONFIG = dict(
        dsn=os.getenv("DATABASE_URL"),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )
else:
    DB_CONFIG = dict(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode=os.getenv("DB_SSLMODE", "require")
    )

def run_sql_file(cursor, filepath):
    print(f"Applying {filepath}...")
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        # Filter out psql meta-commands (starting with \)
        # and accumulate SQL statements.
        sql_commands = []
        current_command = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('\\') or stripped.startswith('--') or not stripped:
                continue
            
            current_command.append(line)
            if stripped.endswith(';'):
                sql_commands.append("".join(current_command))
                current_command = []
                
        # Execute each command
        for cmd in sql_commands:
            try:
                cursor.execute(cmd)
            except Exception as e:
                # If "relation already exists", we might want to ignore it
                if "already exists" in str(e):
                    print(f"Notice: {e}")
                else:
                    raise e
                    
        print(f"Successfully applied {filepath}")
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
    except Exception as e:
        print(f"Error executing {filepath}: {e}")
        raise e

def migrate():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Apply Root Schema (stocksim_schema.sql)
        # This usually contains the base tables.
        run_sql_file(cur, "stocksim_schema.sql")
        
        # 2. Apply Backend Schema (portfolio_schema.sql)
        # This contains the game logic tables.
        run_sql_file(cur, "backend/portfolio_schema.sql")
        
        conn.commit()
        conn.close()
        print("Migration complete!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        print("Check your .env variables and ensure your IP is allowed in Supabase.")

if __name__ == "__main__":
    migrate()
