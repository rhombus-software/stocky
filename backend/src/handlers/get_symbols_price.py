import yfinance as yf

def get_symbols_price(symbols):
    print("Fetching details from yfinance for symbols:", symbols)
    prices = {}
    tick = yf.download(symbols, period="2d", interval="1d")['Close']
    print(tick)
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.fast_info['last_price']
            name = ticker.info.get('shortName') or ticker.info.get('longName') or symbol
            print(current_price)
            print(f"Retrieved price for {symbol}: {current_price}")
            prev_day = tick[symbol].iloc[0]
            print(prev_day)
            change = ((current_price - prev_day) / prev_day) * 100
            print(change)
            prices[symbol] = {
                "name": name,
                "current_price": current_price,
                "change": change
            }

        except Exception as e:
            print(f"Error occurred while fetching price for {symbol}: {e}")
            prices[symbol] = None  # Handle errors gracefully
    return prices