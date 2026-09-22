import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.DB import DB  # Import the DB class from the shared module
from shared.Logger import get_logger  # Import the logger from the shared module
import pandas as pd

logger = get_logger(__name__)  # Create a logger for this module

class MACD:
    def __init__(self, data, short_period=12, long_period=26, signal_period=9):
        self.db = DB()  # Initialize the DB instance for use in the class
        self.short_period = short_period
        self.long_period = long_period
        self.signal_period = signal_period
        self.macd_lookback_days = 10
        self.data = data


    def calculate_macd(self, close: pd.Series) -> tuple[pd.Series, pd.Series]:
        logger.info(f"Calculating MACD for close prices with short_period={self.short_period}, long_period={self.long_period}, signal_period={self.signal_period}")
        ema_fast = close.ewm(span=self.short_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.long_period, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()
        return macd, signal

    def check_macd_crossover_below_zero(
        self,
        macd: pd.Series,
        signal: pd.Series,
    ) -> tuple[bool, pd.Timestamp | None]:
        if len(macd) < self.macd_lookback_days + 2:
            return False, None

        for i in range(1, self.macd_lookback_days + 1):
            prev_idx = -i - 1
            curr_idx = -i
            crossed_above = (
                macd.iloc[prev_idx] <= signal.iloc[prev_idx]
                and macd.iloc[curr_idx] > signal.iloc[curr_idx]
            )
            below_zero = macd.iloc[curr_idx] < 0 and signal.iloc[curr_idx] < 0
            if crossed_above and below_zero:
                return True, macd.index[curr_idx]

        return False, None

    def analyze(self):
        results: list[dict] = []
        for row in self.data.itertuples():
            symbol = row.symbol
            raw_value = row.value
            if isinstance(raw_value, str):
                try:
                    raw_value = json.loads(raw_value)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Could not parse historical data for {symbol}")
                    continue

            price_data = pd.DataFrame(raw_value)
            if not price_data.empty and "Date" in price_data.columns:
                price_data.set_index("Date", inplace=True)
            isin = row.isin
            if price_data is not None and not price_data.empty:
                logger.info(f"Data fetched for {symbol}, processing...")
                macd, signal = self.calculate_macd(price_data['Close'])
                crossed_below_zero, crossover_date = self.check_macd_crossover_below_zero(macd, signal)
                current_price = price_data['Close'].iloc[-1]
                results.append({
                    "symbol": symbol,
                    "isin": isin,
                    "crossed_below_zero": crossed_below_zero,
                    "crossover_date": crossover_date,
                    "current_price": current_price
                })

                # For example, you could calculate the MACD line, signal line, and histogram
                # Then you could generate buy/sell signals based on the MACD strategy
            else:
                logger.warning(f"No data available for {symbol}")

        return results

if __name__ == "__main__":
    db = DB()
    data = db.read_all_symbols()
    strat = MACD(data=data)
    result=strat.analyze()
    strat.db.write_csv("reports", f"macd/ind-mse{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv", result)
