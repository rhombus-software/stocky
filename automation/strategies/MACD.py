import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.DB import DB  # Import the DB class from the shared module
from shared.Logger import get_logger  # Import the logger from the shared module


logger = get_logger(__name__)  # Create a logger for this module
class MACD:
    def __init__(self, short_period=12, long_period=26, signal_period=9, catalog='ind-nse-stocks.csv'):
        self.short_period = short_period
        self.long_period = long_period
        self.signal_period = signal_period
        self.catalog_file_path = catalog
        self.symbols = self.load_symbols_from_catalog()

    def load_symbols_from_catalog(self):
        try:
            db = DB()  # Create a default DB instance using environment variables
            logger.info(f"Loading symbols from catalog: {self.catalog_file_path}")
            df = db.read_csv("stock_lists", self.catalog_file_path)
            symbols = df['SYMBOL'].tolist()
            logger.info(f"Catalog loaded successfully with {len(symbols)} symbols.")
            return symbols
        except Exception as e:
            logger.error(f"Error loading symbols from catalog: {e}")
            return []


if __name__ == "__main__":
    strat = MACD()
    print(strat.symbols[:10])
