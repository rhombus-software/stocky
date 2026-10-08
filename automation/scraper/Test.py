from concurrent.futures import ThreadPoolExecutor
import json
import os
import pandas as pd

STOCKS = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "WIPRO", "TATAMOTORS"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def scrape_stock(symbol: str):
    url = f"https://www.screener.in/company/{symbol}/consolidated/#shareholding"
    # Screener allows read_html or direct GET request
    dfs = pd.read_html(url, match="Promoters")
    if dfs:
        df = dfs[0]
        records = df.to_dict(orient="records")
        out_path = f"result/{symbol}_shareholding_pattern.json"
        os.makedirs("result", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"symbol": symbol, "data": records}, f, indent=2)
        return symbol, True
    return symbol, False

# Run 5 stocks concurrently without browser overhead
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(scrape_stock, STOCKS))
    print("Scraped:", results)
