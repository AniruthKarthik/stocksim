
import sys
import os
import requests
import psycopg2
import time
import json
import subprocess
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from backend.db_conn import get_db_connection
except ImportError as e:
    print(f"Could not import backend.db_conn: {e}. Ensure you are in the project root.")

# Configuration
API_URL = "http://localhost:8000"
DB_NAME = os.getenv("DB_NAME", "stocksim")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, status="INFO"):
    color = RESET
    if status == "SUCCESS": color = GREEN
    elif status == "ERROR": color = RED
    elif status == "WARNING": color = YELLOW
    print(f"{color}[{status}] {msg}{RESET}")

def check_process_list():
    log("Checking for running Python processes...", "INFO")
    try:
        # Simple grep for 'main:app' or 'uvicorn'
        result = subprocess.check_output("ps aux | grep -E 'uvicorn|main.py|fastapi'", shell=True).decode()
        print(result)
    except Exception as e:
        log(f"Failed to list processes: {e}", "WARNING")

def check_db_connection():
    log("Checking Database Connection (via Application Logic)...", "INFO")
    try:
        # Method 1: App Logic
        from backend.db_conn import get_db_connection
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            log(f"Database connected (App Logic): {version.split()[0]}", "SUCCESS")
        return True
    except Exception as e:
        log(f"App Logic Connection failed: {e}", "ERROR")
        
        # Method 2: Raw Fallback
        log("Retrying with raw psycopg2 (sslmode=require)...", "INFO")
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
                sslmode='require'
            )
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            conn.close()
            log(f"Database connected (Raw Fallback): {version.split()[0]}", "SUCCESS")
            return True
        except Exception as e2:
            log(f"Raw Fallback failed: {e2}", "ERROR")
            return False

def check_api_health():
    log("Checking Backend API Health...", "INFO")
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            log("Backend API is reachable.", "SUCCESS")
            return True
        else:
            log(f"Backend API returned status {response.status_code}", "ERROR")
            return False
    except requests.exceptions.ConnectionError:
        log("Backend API Connection Refused. The server is likely NOT running.", "ERROR")
        return False

def simulate_frontend_flow():
    log("Simulating Frontend 'Launch Simulator' Flow...", "INFO")
    
    # 1. Create User
    username = f"test_user_{int(time.time())}"
    log(f"Step 1: Creating User '{username}'...", "INFO")
    try:
        res = requests.post(f"{API_URL}/users", json={"username": username})
        if res.status_code != 200:
            log(f"Failed to create user: {res.text}", "ERROR")
            return
        user_data = res.json()
        user_id = user_data['user_id']
        log(f"User created. ID: {user_id}", "SUCCESS")
    except Exception as e:
        log(f"Exception during user creation: {e}", "ERROR")
        return

    # 2. Create Portfolio
    log(f"Step 2: Creating Portfolio for User {user_id}...", "INFO")
    try:
        res = requests.post(f"{API_URL}/portfolio/create", json={
            "user_id": user_id,
            "name": "Test Portfolio",
            "currency_code": "USD"
        })
        if res.status_code != 200:
            log(f"Failed to create portfolio: {res.text}", "ERROR")
            return
        port_data = res.json()
        portfolio_id = port_data['id']
        log(f"Portfolio created. ID: {portfolio_id}", "SUCCESS")
    except Exception as e:
        log(f"Exception during portfolio creation: {e}", "ERROR")
        return

    # 3. Start Simulation
    log(f"Step 3: Starting Simulation...", "INFO")
    try:
        res = requests.post(f"{API_URL}/simulation/start", json={
            "user_id": user_id,
            "portfolio_id": portfolio_id,
            "start_date": "2023-01-01",
            "monthly_salary": 5000,
            "monthly_expenses": 2000
        })
        if res.status_code != 200:
            log(f"Failed to start simulation: {res.text}", "ERROR")
            return
        sim_data = res.json()
        log(f"Simulation started successfully.", "SUCCESS")
    except Exception as e:
        log(f"Exception during simulation start: {e}", "ERROR")
        return

    log("Full Frontend Flow Simulation Complete", "SUCCESS")

def main():
    print("=== STOCKSIM DIAGNOSTIC TOOL ===")
    
    check_process_list()
    
    db_ok = check_db_connection()
    api_ok = check_api_health()
    
    if api_ok:
        simulate_frontend_flow()
    else:
        print("\n[SUGGESTION] The backend API seems down. Try running:")
        print("uvicorn backend.main:app --reload")

if __name__ == "__main__":
    main()
