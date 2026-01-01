from .db_prices import get_adj_close


def simulate_invest(amount: float, symbol: str, buy_date: str, sell_date: str):
    """
    Simulate: If I invest <amount> at <buy_date>,
    how much is it worth at <sell_date>?
    """

    # get prices from DB
    buy_price = get_adj_close(symbol, buy_date)
    sell_price = get_adj_close(symbol, sell_date)

    # if any price missing → return None
    if buy_price is None or sell_price is None:
        return None

    # calculate number of units bought
    units = amount / buy_price

    # value on sell date
    value = units * sell_price

    return round(value, 2)

