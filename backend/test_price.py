from .db_prices import get_adj_close

price = get_adj_close("APPLE", "2015-01-05")
print(price)

