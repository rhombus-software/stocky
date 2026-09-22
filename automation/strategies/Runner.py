import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from shared.Logger import get_logger
from shared.DB import DB
from strategies.RSI import RSI
from strategies.MACD import MACD

logger = get_logger(__name__)
db = DB()
class Runner:
    def __init__(self):
        self.strategies = []
        logger.info("Fetching data")
        self.data = db.read_all_symbols()
    
    def set_strategies(self, strategies):
        self.strategies = strategies
        
    def run(self):
        logger.info("Running strategies")
        for strategy in self.strategies:
            strategy_name = strategy.__class__.__name__
            logger.info(f"Running strategy: {strategy_name}")
            results = strategy.analyze()
            if results:
                db.write_csv(
                    "reports",
                    f"{strategy_name}/{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    results
                )
                logger.info("Completed")

if __name__ == '__main__':
    runner = Runner()
    print(runner.data)
    runner.set_strategies([RSI(data=runner.data), MACD(data=runner.data)])
    runner.run()