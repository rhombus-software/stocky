import yfinance as yf
import sys
from requests import get
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.DB import DB
db = DB()
from shared.Logger import get_logger
logger = get_logger(__name__)


def get_data():
    logger.info("Fetching data")
    symbols_catalog = db.read_all_symbols()
    logger.info(f"Fetched {len(symbols_catalog)} symbols")
    symbols_lists = symbols_catalog['symbol'].to_list()
    tickers = yf.Tickers(" ".join(symbols_lists))
    return tickers.tickers

# Helper function to safely extract row data
def get_row(df, names):
    for name in names:
        if name in df.index:
            return df.loc[name]
    return pd.Series(dtype=float)


def transform(tickers_data):
    all_companies_data = []
    for symbol, stock in tickers_data.items():
        try:
            logger.info(f"Processing data for {symbol}...")
            
            # Access quarterly statements
            inc = stock.quarterly_income_stmt
            bs = stock.quarterly_balance_sheet
            cf = stock.quarterly_cashflow
            
            if inc.empty or bs.empty or cf.empty:
                continue

            # Extract core metrics
            revenue = get_row(inc, ['Total Revenue', 'Operating Revenue'])
            net_income = get_row(inc, ['Net Income Common Stockholders', 'Net Income'])
            operating_income = get_row(inc, ['Operating Income'])
            
            total_assets = get_row(bs, ['Total Assets'])
            total_liabilities = get_row(bs, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
            stockholder_equity = get_row(bs, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
            total_debt = get_row(bs, ['Total Debt'])
            cash_and_equiv = get_row(bs, ['Cash Cash Equivalents And Short Term Investments', 'Cash And Cash Equivalents'])
            
            operating_cash_flow = get_row(cf, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
            capital_expenditures = get_row(cf, ['Capital Expenditure', 'Capital Expenditures'])
            free_cash_flow = get_row(cf, ['Free Cash Flow'])

            # Calculate ratios & margins
            profit_margin = (net_income / revenue) * 100
            operating_margin = (operating_income / revenue) * 100
            debt_to_equity = total_debt / stockholder_equity
            roe = (net_income / stockholder_equity) * 100

            metrics_dict = {
                'Total Revenue': revenue,
                'Net Income': net_income,
                'Net Profit Margin (%)': profit_margin,
                'Operating Margin (%)': operating_margin,
                'Total Assets': total_assets,
                'Total Liabilities': total_liabilities,
                'Stockholders Equity': stockholder_equity,
                'Total Debt': total_debt,
                'Cash & Short Term Investments': cash_and_equiv,
                'Debt to Equity Ratio': debt_to_equity,
                'Return on Equity - ROE (%)': roe,
                'Operating Cash Flow': operating_cash_flow,
                'Capital Expenditures': capital_expenditures,
                'Free Cash Flow': free_cash_flow,
            }

            # Build row formatted as: SYMBOL | metric-name-YYYY-MM-DD ...
            company_row = {'SYMBOL': symbol}
            
            for metric_name, series in metrics_dict.items():
                if not series.empty:
                    for date, value in series.items():
                        date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
                        col_name = f"{metric_name.lower().replace(' ', '-')}-{date_str}"
                        company_row[col_name] = value

            all_companies_data.append(company_row)
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    return pd.DataFrame(all_companies_data)

if __name__ == "__main__":
    tickers = get_data()
    final_df = transform(tickers)
    db.write_csv("reports", "financials/ind-stocs.csv", final_df)
    logger.info("Completed")
    

