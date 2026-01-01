import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[TEST] {msg}")

def run_validation():
    try:
        # 1. Check API Health
        try:
            r = requests.get(BASE_URL + "/")
            if r.status_code != 200:
                log(f"Health check failed: {r.text}")
                sys.exit(1)
            log("API is healthy.")
        except requests.exceptions.ConnectionError:
            log(f"❌ Could not connect to {BASE_URL}. Is the server running? Run 'uvicorn backend.main:app --reload' in another terminal.")
            sys.exit(1)

        # 2. Create User
        username = f"validator_{int(time.time())}"
        r = requests.post(BASE_URL + "/users", json={"username": username})
        if r.status_code != 200:
            log(f"Create user failed: {r.text}")
            sys.exit(1)
        user_id = r.json()["user_id"]
        log(f"User created: {username} (ID: {user_id})")

        # 3. Create Portfolio
        r = requests.post(BASE_URL + "/portfolio/create", json={"user_id": user_id, "name": "ValidationPort"})
        if r.status_code != 200:
            log(f"Create portfolio failed: {r.text}")
            sys.exit(1)
        portfolio_id = r.json()["id"]
        log(f"Portfolio created: ValidationPort (ID: {portfolio_id})")

        # 4. Start Simulation (2020-01-01)
        # Salary: 1000, Expenses: 500 -> Net +500/month
        sim_data = {
            "user_id": user_id,
            "portfolio_id": portfolio_id,
            "start_date": "2020-01-01",
            "monthly_salary": 1000,
            "monthly_expenses": 500
        }
        r = requests.post(BASE_URL + "/simulation/start", json=sim_data)
        if r.status_code != 200:
            log(f"Start simulation failed: {r.text}")
            sys.exit(1)
        log("Simulation started at 2020-01-01")

        # 5. Buy Asset (Should default to 2020-01-01)
        buy_data = {
            "portfolio_id": portfolio_id,
            "symbol": "APPLE",
            "quantity": 10
        }
        r = requests.post(BASE_URL + "/portfolio/buy", json=buy_data)
        if r.status_code != 200:
            log(f"Buy failed: {r.text}")
            sys.exit(1)
        log("Bought 10 APPLE")

        # 6. Advance Time (Move 3 months -> 2020-04-01)
        # Net income should be 500 * 3 = 1500 added.
        fwd_data = {
            "portfolio_id": portfolio_id,
            "target_date": "2020-04-01"
        }
        r = requests.post(BASE_URL + "/simulation/forward", json=fwd_data)
        if r.status_code != 200:
            log(f"Advance time failed: {r.text}")
            sys.exit(1)
        res_json = r.json()
        log(f"Time advanced: {res_json['months_passed']} months passed. Cash added: {res_json['cash_added']}")
        
        if res_json['months_passed'] != 3:
            log("❌ Month calculation wrong!")
            sys.exit(1)
        if res_json['cash_added'] != 1500.0:
            log(f"❌ Cash calculation wrong! Expected 1500.0, got {res_json['cash_added']}")
            sys.exit(1)

        # 7. Check Status & Value
        r = requests.get(f"{BASE_URL}/simulation/status?portfolio_id={portfolio_id}")
        if r.status_code != 200:
            log(f"Get status failed: {r.text}")
            sys.exit(1)
        status = r.json()
        log(f"Final Status: Date={status['session']['sim_date']}, Portfolio Value={status['portfolio_value']['total_value']}")
        
        if status['session']['sim_date'] != "2020-04-01":
            log("❌ Sim date mismatch!")
            sys.exit(1)

        log("✅ Full flow validation passed successfully.")

    except Exception as e:
        log(f"❌ Validation crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
