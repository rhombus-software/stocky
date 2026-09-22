import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from shared.Logger import get_logger
from shared.DB import DB
from strategies.RSI import RSI
logger = get_logger(__name__)
db = DB()
class Runner:
    def __init__(self):
        self.strategies = []
        logger.info("Fetching data")
        self.data = db.read_all_symbols()
    
    def set_strategies(self, strategies):
        self.strategies = strategies
        
    def run():
        loogger.info("Running strategiess")
        for strategy in self.strategies:
            logger.info(f"Running strategies {strategy.name}")
            data = strategy.analyze()
            print(data.head(2))

if __name__ == '__main__':
    runner = Runner()
    print(runner.data)
    runner.set_strategies([RSI(data=runner.data)])
    runner.run()