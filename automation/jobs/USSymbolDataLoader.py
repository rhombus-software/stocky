import sys
from requests import get

import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.DB import DB

db = DB()
def get_data():
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.nasdaq.com",
            "Referer": "https://www.nasdaq.com/",
            }
    url = 'https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=8000&offset=0'
    data = get(url=url, headers=headers).json()
    return data

def transform_data(data):
    rows = data['data']['table']['rows']
    df = pd.DataFrame(rows)
    df = df.query("marketCap != 'NA'")
    df['ISIN Code'] = 'US_NASDAQ_' + df['symbol']
    df['Country'] ='US'
    df = df.drop(columns=['url'], errors='ignore').rename(
        columns={
            "symbol": "SYMBOL",
            "companyName": "NAME",
            "lastsale": "PRICE",
        }
    )
    print(df.columns)
    return df

if __name__ == "__main__":
    data = get_data()
    df = transform_data(data)
    db.write_csv("stock_lists",'us-nasdaq-stocks.csv',df[:100])
    print("Completeef")