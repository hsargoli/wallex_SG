class BaseStrategy:
    # Interface for strategy logic
    def on_tick(self, price: float):
        raise NotImplementedError

class SimpleTrendStrategy(BaseStrategy):
    # Buy below 100, Sell above 101
    def __init__(self):
        self.in_position = False

    def on_tick(self, price: float):
        if price < 100.0 and not self.in_position:
            self.in_position = True
            return "BUY"
        elif price > 101.0 and self.in_position:
            self.in_position = False
            return "SELL"
        return "HOLD"
