import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.DataFetcher import DataFetcher

from strategies.MACD import MACD
from strategies.RSI import RSI
from strategies.ValueInvesting import ValueInvesting


def run_strategies() -> dict[str, list[dict]]:
	"""Fetch shared data once, then run every configured strategy."""
	data_fetcher = DataFetcher()
	macd = MACD(data_fetcher=data_fetcher)
	rsi = RSI(data_fetcher=data_fetcher)
	value_investing = ValueInvesting(data_fetcher=data_fetcher)

	symbols = set(macd.symbols) | set(rsi.symbols)
	price_data = {
		f"{symbol}.NS": data_fetcher.fetch_price_data(f"{symbol}.NS")
		for symbol in symbols
	}

	return {
		"macd": macd.analyze(price_data),
		"rsi": rsi.analyze(price_data),
		"value_investing": value_investing.analyze(),
	}


if __name__ == "__main__":
	results = run_strategies()
	print({name: len(data) for name, data in results.items()})
