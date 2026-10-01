from app.domain.strategy import BaseStrategy
from app.domain.repository import MarketDataRepository

class Simulator:
    def __init__(self, strategy: BaseStrategy, repo: MarketDataRepository):
        self.strategy = strategy
        self.repo = repo
        self.balance = 1000.0  # Initial capital
        self.position = 0.0

    def run(self, symbol: str, start_date: str, end_date: str):
        prices = self.repo.get_prices(symbol, start_date, end_date)
        total_pnl = 0.0
        
        for price in prices:
            action = self.strategy.on_tick(price)
            if action == "BUY" and self.balance >= price:
                self.position = self.balance / price
                self.balance = 0.0
            elif action == "SELL" and self.position > 0:
                new_balance = self.position * price
                total_pnl += (new_balance - 1000.0) # Simple PnL calculation
                self.balance = new_balance
                self.position = 0.0
        
        return {"final_balance": self.balance + (self.position * prices[-1]), "total_pnl": total_pnl}
