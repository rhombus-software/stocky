import yfinance as yf

def get_symbols_price(symbols):
    print("Fetching details from yfinance for symbols:", symbols)
    prices = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info['last_price']
            print(f"Retrieved price for {symbol}: {price}")
            prices[symbol] = price
        except Exception as e:
            print(f"Error occurred while fetching price for {symbol}: {e}")
            prices[symbol] = None  # Handle errors gracefully
    return prices