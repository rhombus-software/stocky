import asyncio
import json
import sys
from functools import partial
from pathlib import Path
from typing import List, Dict, Any
import yfinance as yf
from pandas import MultiIndex
sys.path.append(str(Path(__file__).resolve().parent.parent))
from shared.Logger import get_logger 
from shared.DB import DB

logger = get_logger("Data loader")
db = DB()
from json import loads

class HistoricDataLoader:
    def __init__(self, catalog: List[Dict[str, str]]):
        self.catalog = catalog

    async def fetch_symbol_data(self, isin: str, symbol: str) -> Dict[str, Any]:
        """Fetch historical data for a single symbol asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            logger.info(f"Fetching data for {symbol}")
            download_func = partial(yf.download, symbol, period="max", progress=False)
            df = await loop.run_in_executor(None, download_func)
            if df is not None and not df.empty:
                if isinstance(df.columns, MultiIndex):
                    df.columns = df.columns.droplevel(1)
                    df.reset_index(inplace=True)
                    return {"isin": isin, "symbol": symbol, "data": loads(df.to_json(orient="records", date_format="iso")), "status": "success"}
            logger.warning(f"No data for {symbol}")
            return {"isin": isin, "symbol": symbol, "status": "no_data"}
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return {"isin": isin, "symbol": symbol, "status": "error", "error": str(e)}

    async def fetch_batch(self, catalog: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Fetch data for multiple catalog entries concurrently."""
        tasks = [self.fetch_symbol_data(item["isin"], item["symbol"]) for item in catalog]
        return await asyncio.gather(*tasks)

    def load_data(self, table_name: str = "stock_historical") -> Dict[str, Any]:
        """Load historical data for catalog symbols and store in database."""
        if not self.catalog:
            return {"success": False, "error": "Empty catalog"}
        try:
            return asyncio.run(self._load_async(table_name))
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {"success": False, "error": str(e)}

    async def _load_async(self, table_name: str) -> Dict[str, Any]:
        """Asynchronously load data in batches of 500 symbols."""
        results = {
            "success": True,
            "total": len(self.catalog),
            "successful": 0,
            "failed": 0,
            "failed_symbols": [],
            "errors": []
        }
        
        batch_size = 500
        for i in range(0, len(self.catalog), batch_size):
            batch = self.catalog[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            logger.info(f"Processing batch {batch_num}: {len(batch)} symbols")
            
            batch_results = await self.fetch_batch(batch)
            
            # Collect successful results for batch write
            records_to_write = []
            for result in batch_results:
                symbol = result["symbol"]
                if result["status"] == "success":
                    records_to_write.append((result["isin"], symbol, result["data"]))
                else:
                    results["failed"] += 1
                    results["failed_symbols"].append(symbol)
                    error_msg = result.get("error", "Unknown error")
                    results["errors"].append({"symbol": symbol, "error": error_msg})
            print(records_to_write[1])
            if records_to_write:
                try:
                    db.write_jsonb_batch_to_table(table_name, records_to_write)
                    results["successful"] += len(records_to_write)
                    logger.info(f"Batch {batch_num}: Successfully wrote {len(records_to_write)} records")
                except Exception as e:
                    for isin, symbol, _ in records_to_write:
                        results["failed"] += 1
                        results["failed_symbols"].append(symbol)
                        results["errors"].append({"isin": isin, "symbol": symbol, "error": str(e)})
                    logger.error(f"Error writing batch {batch_num}: {e}")
        
        logger.info(f"Completed: {results['successful']} successful, {results['failed']} failed")
        return results

if __name__ == "__main__":
    # Example usage
    data = db.read_csv("stock_lists", "ind-nse-nifty100-stocks.csv")
    catalog = [
        {"isin": isin, "symbol": f"{symbol}.NS"}
        for isin, symbol in data[["ISIN Code", "SYMBOL"]].itertuples(index=False, name=None)
        if isin and symbol
    ][:2]
    loader = HistoricDataLoader(catalog)
    result = loader.load_data()
    print(result)