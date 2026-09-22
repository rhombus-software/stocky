import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd

from shared.DB import DB
from shared.Logger import get_logger


logger = get_logger(__name__)

class RSI:
	def __init__(
		self,
		data,
		period=14,
		oversold=20,
		overbought=60,
	):
		self.period = period
		self.oversold = oversold
		self.overbought = overbought
		self.rsi_lookback_days = 10
		self.data = data

	def calculate_rsi(self, close: pd.Series) -> pd.Series:
		logger.info(f"Calculating RSI with period={self.period}")
		change = close.diff()
		gains = change.clip(lower=0)
		losses = -change.clip(upper=0)
		average_gain = gains.ewm(
			alpha=1 / self.period,
			adjust=False,
			min_periods=self.period,
		).mean()
		average_loss = losses.ewm(
			alpha=1 / self.period,
			adjust=False,
			min_periods=self.period,
		).mean()
		relative_strength = average_gain / average_loss
		return 100 - (100 / (1 + relative_strength))

	def check_rsi_recovery(
		self,
		rsi: pd.Series,
	) -> tuple[bool, pd.Timestamp | None]:
		if len(rsi) < self.rsi_lookback_days + 2:
			return False, None

		for i in range(1, self.rsi_lookback_days + 1):
			previous = rsi.iloc[-i - 1]
			current = rsi.iloc[-i]
			crossed_above_oversold = (
				previous <= self.oversold and current > self.oversold
			)
			if crossed_above_oversold:
				return True, rsi.index[-i]

		return False, None

	def analyze(self):
		results: list[dict] = []
		for row in self.data.itertupel():
			symbol = row.symbol
			price_data = pd.from_json(row.value)
			isin = row.isin
			if price_data is not None:
				logger.info(f"Data fetched for {symbol}, processing...")
				rsi = self.calculate_rsi(df["Close"])
				recovered_from_oversold, recovery_date = self.check_rsi_recovery(rsi)
				current_rsi = rsi.iloc[-1]
				results.append(
					{
						"isin": isin,
						"symbol": symbol,
						"recovered_from_oversold": recovered_from_oversold,
						"recovery_date": recovery_date,
						"is_overbought": current_rsi >= self.overbought,
						"current_rsi": current_rsi,
						"current_price": price_data["Close"].iloc[-1],
					}
				)
                
			else:
				logger.warning(f"No data available for {symbol}")
		return results


if __name__ == "__main__":
	strat = RSI()
	result = strat.analyze()
	strat.db.write_csv(
		"reports",
		f"rsi/ind-mse{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
		result,
	)
