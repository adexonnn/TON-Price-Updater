import os

def read_previous_price(price_file):
    if os.path.exists(price_file):
        with open(price_file, "r") as file:
            return float(file.read().strip())
    return None

def save_current_price(price_file, price):
    with open(price_file, "w") as file:
        file.write(str(price))

def format_market_cap(market_cap):
    if market_cap >= 1_000_000_000:
        return f"{market_cap / 1_000_000_000:.1f}B"
    elif market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.1f}M"
    return str(market_cap)
