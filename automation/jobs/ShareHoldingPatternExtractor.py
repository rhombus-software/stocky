import json
from pathlib import Path
import pandas as pd
import robot
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
ROBOT_FILE = BASE_DIR / "scraper" / "screener_scraper.robot"
OUTPUT_DIR = BASE_DIR / "scraper" / "result"
LOGS_DIR = OUTPUT_DIR / "logs"

sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.DB import DB

db = DB()

def get_symbol():
    symbol_list = db.read_all_symbols()
    return symbol_list



def extract_shareholding_patterns(
    stocks: list[str] | None = None,
    cleanup_json: bool = True,
) -> pd.DataFrame:
    """
    Runs the screener scraper robot suite, aggregates the shareholding pattern
    table data for all stocks into a single pandas DataFrame, and returns it.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    stocks_arg = ",".join(stocks)

    robot.run(
        str(ROBOT_FILE),
        variable=[
            f"STOCKS:{stocks_arg}",
            f"OUTPUT_DIR:{OUTPUT_DIR}",
        ],
        outputdir=str(LOGS_DIR),
    )

    records: list[dict] = []
    for symbol in stocks:
        json_file = OUTPUT_DIR / f"{symbol}_shareholding_pattern.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                data = content.get("data", [])
                for row in data:
                    records.append({"SYMBOL": symbol, **row})
            finally:
                if cleanup_json:
                    json_file.unlink(missing_ok=True)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


if __name__ == "__main__":
    symbol_catalog = get_symbol()
    symbol_list = symbol_catalog['symbol'].str.split(".").str[0].tolist()
    print(symbol_list)
    df = extract_shareholding_patterns(symbol_list)
    print(df)
    df.to_csv("ShareHoldingPattern.csv")