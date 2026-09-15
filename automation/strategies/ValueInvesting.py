import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd

from shared.DataFetcher import DataFetcher
from shared.DB import DB
from shared.Logger import get_logger


logger = get_logger(__name__)


#cobst
CATALOG_FILE_NAME='ind-nse-nifty100-stocks.csv'
class ValueInvesting:
	"""Fetch fundamental metrics used to screen value-investing stocks.

	Yahoo Finance does not consistently publish an Indian FII/FPI-specific
	series. The ownership fields therefore use Yahoo's institutional-holder
	data as the closest available proxy and keep that limitation explicit in
	the output field names.
	"""

	def __init__(self, catalog: str = CATALOG_FILE_NAME, data_fetcher=None) -> None:
		self.data_fetcher = data_fetcher or DataFetcher()
		self.db = self.data_fetcher.db
		self.catalog_file_path = catalog
		self.symbols = self.data_fetcher.load_symbols(catalog)

	@staticmethod
	def _number(value: Any) -> float | None:
		"""Convert pandas and NumPy scalars to a CSV/JSON-safe number."""
		if value is None or pd.isna(value):
			return None
		try:
			return float(value)
		except (TypeError, ValueError):
			return None

	@staticmethod
	def _statement_value(
		statement: pd.DataFrame,
		row_names: tuple[str, ...],
		column: Any,
	) -> float | None:
		"""Read the first matching row from a Yahoo quarterly statement."""
		for row_name in row_names:
			if row_name in statement.index:
				return ValueInvesting._number(statement.at[row_name, column])
		return None

	def _quarterly_profits(self, income_statement: pd.DataFrame) -> list[dict[str, Any]]:
		"""Return quarterly revenue, net profit, and EPS in report order."""
		if income_statement.empty:
			return []

		quarters = []
		for quarter in income_statement.columns:
			quarters.append(
				{
					"quarter": pd.Timestamp(quarter).strftime("%Y-%m-%d"),
					"revenue": self._statement_value(
						income_statement, ("Total Revenue",), quarter
					),
					"net_profit": self._statement_value(
						income_statement, ("Net Income", "Net Income Common Stockholders"), quarter
					),
					"diluted_eps": self._statement_value(
						income_statement, ("Diluted EPS", "Basic EPS"), quarter
					),
				}
			)
		return quarters

	def _quarterly_cash_flows(self, cash_flow: pd.DataFrame) -> list[dict[str, Any]]:
		"""Return the key cash-flow lines for each available quarter."""
		if cash_flow.empty:
			return []

		cash_flows = []
		for quarter in cash_flow.columns:
			cash_flows.append(
				{
					"quarter": pd.Timestamp(quarter).strftime("%Y-%m-%d"),
					"operating_cash_flow": self._statement_value(
						cash_flow, ("Operating Cash Flow",), quarter
					),
					"free_cash_flow": self._statement_value(
						cash_flow, ("Free Cash Flow",), quarter
					),
					"capital_expenditure": self._statement_value(
						cash_flow, ("Capital Expenditure",), quarter
					),
					"investing_cash_flow": self._statement_value(
						cash_flow, ("Investing Cash Flow",), quarter
					),
					"financing_cash_flow": self._statement_value(
						cash_flow, ("Financing Cash Flow",), quarter
					),
					"ending_cash": self._statement_value(
						cash_flow, ("End Cash Position", "Cash Cash Equivalents And Short Term Investments"), quarter
					),
				}
			)
		return cash_flows

	def _institutional_ownership(self, holders: pd.DataFrame) -> dict[str, float | None]:
		"""Aggregate reported institutional ownership and its period change.

		Yahoo's table has individual institutions and report dates, so the
		change is calculated between the two most recent reported dates.
		"""
		empty_result = {
			"institutional_holding_pct": None,
			"institutional_holding_change_pct": None,
		}
		if holders.empty or "pctHeld" not in holders.columns:
			return empty_result

		data = holders.copy()
		data["pctHeld"] = pd.to_numeric(data["pctHeld"], errors="coerce")
		data = data.dropna(subset=["pctHeld"])
		if data.empty:
			return empty_result

		current = float(data["pctHeld"].sum() * 100)
		result = {"institutional_holding_pct": current, "institutional_holding_change_pct": None}
		if "dateReported" in data.columns:
			data["dateReported"] = pd.to_datetime(data["dateReported"], errors="coerce")
			totals = data.groupby("dateReported", dropna=True)["pctHeld"].sum().sort_index()
			if len(totals) >= 2:
				result["institutional_holding_change_pct"] = float(
					(totals.iloc[-1] - totals.iloc[-2]) * 100
				)
		return result

	@staticmethod
	def _equity_to_debt_ratio(
		balance_sheet: pd.DataFrame,
		column: Any,
		total_debt: float | None,
	) -> float | None:
		"""Calculate the latest total-equity-to-debt ratio.

		A ratio is only reported when both values are available and debt is
		positive. Debt-free companies therefore keep a null ratio instead of
		an infinite value that would not be useful in a CSV report.
		"""
		if balance_sheet.empty or column is None or total_debt is None or total_debt <= 0:
			return None

		total_equity = ValueInvesting._statement_value(
			balance_sheet,
			(
				"Stockholders Equity",
				"Common Stock Equity",
				"Total Equity Gross Minority Interest",
			),
			column,
		)
		if total_equity is None:
			return None
		return total_equity / total_debt

	def fetch_symbol_data(self, symbol: str) -> dict[str, Any] | None:
		"""Fetch one stock's quote, statements, and ownership data."""
		try:
			ticker = self.data_fetcher.fetch_ticker(symbol)
			info = ticker.info
			income_statement = ticker.quarterly_income_stmt
			balance_sheet = ticker.quarterly_balance_sheet
			cash_flow = ticker.quarterly_cashflow
			ownership = self._institutional_ownership(ticker.institutional_holders)
			latest_balance_sheet_column = (
				balance_sheet.columns[0] if not balance_sheet.empty else None
			)

			total_debt = self._statement_value(
				balance_sheet, ("Total Debt", "Long Term Debt And Capital Lease Obligation"),
				latest_balance_sheet_column,
			)
			if total_debt is None:
				total_debt = self._number(info.get("totalDebt"))

			market_cap = self._number(info.get("marketCap"))
			if market_cap is None:
				market_cap = self._number(getattr(ticker.fast_info, "market_cap", None))

			return {
				"symbol": symbol.removesuffix(".NS"),
				"market_cap": market_cap,
				"eps": self._number(info.get("trailingEps")),
				"total_debt": total_debt,
				"debt_free": total_debt is not None and total_debt <= 0,
				"equity_to_debt_ratio": self._equity_to_debt_ratio(
					balance_sheet, latest_balance_sheet_column, total_debt
				),
				"quarterly_profit": json.dumps(self._quarterly_profits(income_statement)),
				"cash_flows": json.dumps(self._quarterly_cash_flows(cash_flow)),
				**ownership,
			}
		except Exception as exc:
			logger.error(f"Error fetching fundamental data for {symbol}: {exc}")
			return None

	def analyze(self) -> list[dict[str, Any]]:
		"""Fetch fundamentals for every symbol in the configured catalog."""
		results = []
		for symbol in self.symbols:
			yahoo_symbol = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
			stock_data = self.fetch_symbol_data(yahoo_symbol)
			if stock_data is not None:
				results.append(stock_data)
			else:
				logger.warning(f"No fundamental data available for {symbol}")
		return results


if __name__ == "__main__":
	strategy = ValueInvesting()
	result = strategy.analyze()
	strategy.db.write_csv(
		"reports",
		f"value-investing/ind-nse-{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
		result,
	)
