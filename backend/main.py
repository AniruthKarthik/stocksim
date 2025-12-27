from fastapi import FastAPI
from simulator import simulate_invest

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/simulate")
def simulate(
    amount: float,
    symbol: str,
    buy: str,
    sell: str
):
    result = simulate_invest(amount, symbol.upper(), buy, sell)

    if result is None:
        return {"error": "Invalid symbol or dates"}

    return {
        "amount": amount,
        "symbol": symbol.upper(),
        "buy": buy,
        "sell": sell,
        "future_value": result
    }

