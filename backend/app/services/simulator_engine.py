class Simulator:
    def __init__(self, repository, strategy):
        self.repository = repository
        self.strategy = strategy
        self.initial_balance = 1000.0

    async def run(self, start_date: str, end_date: str, symbol: str = "BTCUSDT"):
        """
        Runs the simulation for a given date range.
        """
        # Repository فعلی sync هست و لیست float برمی‌گردونه
        prices = self.repository.get_prices(symbol, start_date, end_date)

        if not prices:
            return {
                "status": "error",
                "message": "No data found for the selected range",
                "pnl_report": {"final_balance": self.initial_balance, "total_pnl": 0}
            }

        balance = self.initial_balance
        position = 0  # 0: None, 1: Long
        entry_price = 0.0
        trades = []

        for i, current_price in enumerate(prices):
            signal = self.strategy.on_tick(current_price)

            if signal == "BUY" and position == 0:
                position = 1
                entry_price = current_price
                trades.append({"i": i, "side": "BUY", "price": current_price})

            elif signal == "SELL" and position == 1:
                profit_pct = (current_price - entry_price) / entry_price
                balance += balance * profit_pct
                position = 0
                trades.append({"i": i, "side": "SELL", "price": current_price})

        # ------------------------------------------------------------
        # بستن اجباری پوزیشن باز در پایان شبیه‌سازی
        # (تا سود/زیان لحظه‌ای هم در گزارش بیاد)
        # ------------------------------------------------------------
        if position == 1 and entry_price > 0:
            last_price = prices[-1]
            profit_pct = (last_price - entry_price) / entry_price
            balance += balance * profit_pct
            position = 0
            trades.append({
                "i": len(prices) - 1,
                "side": "SELL",
                "price": last_price,
                "forced": True,   # علامت‌گذاری: بستن اجباری
            })

        total_pnl = balance - self.initial_balance

        return {
            "status": "success",
            "symbol": symbol,
            "prices_count": len(prices),
            "trades": trades,
            "open_position": False,
            "pnl_report": {
                "initial_balance": self.initial_balance,
                "final_balance": round(balance, 2),
                "total_pnl": round(total_pnl, 2),
                "pnl_pct": round((total_pnl / self.initial_balance) * 100, 2),
            }
        }
