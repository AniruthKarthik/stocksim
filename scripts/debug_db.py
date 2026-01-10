import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db_conn import get_db_connection

def run_query(query):
    print(f"Running Query: {query}")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    print(f"Columns: {columns}")
                    for row in cur.fetchall():
                        print(row)
                else:
                    print("No results returned.")
                conn.commit()
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_query(sys.argv[1])
    else:
        print("Please provide a query.")