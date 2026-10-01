"""Smart Dispatcher — هر ارز با استراتژی مخصوص خودش."""

import json
from pathlib import Path

from app.domain.entities.candle import Candle
from app.services.bounce_scalper import make_bounce_decision
from app.services.simple_bot import make_simple_decision

CONFIG_PATH = Path("data/strategy_config.json")

# حداقل آستانه‌ها
MIN_AVG_RETURN = 0.3  # حداقل 0.3% میانگین
MIN_STABILITY = 0.5  # حداقل 50% پایداری


class SmartDispatcher:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config = {}
        self.stats = {}  # symbol → {avg, stability, strategy}
        self._load_config(config_path)

    def _load_config(self, path: Path):
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
            for symbol, cfg in data.items():
                strategy = cfg["best_strategy"]
                summary = cfg["summary"][strategy]
                avg = summary["avg_return"]
                stability = summary["stability"]

                # فیلتر: فقط اگه عملکرد قابل قبول بود
                if avg >= MIN_AVG_RETURN and stability >= MIN_STABILITY:
                    self.config[symbol] = strategy
                    self.stats[symbol] = {"avg": avg, "stability": stability, "strategy": strategy}
        except Exception as e:
            print(f"⚠️ Config load error: {e}")

    def get_strategy(self, symbol: str) -> str | None:
        """برگرداندن استراتژی مناسب برای یک نماد."""
        return self.config.get(symbol)

    def list_active(self) -> dict:
        """لیست نمادهای فعال با استراتژی‌ها."""
        return dict(self.config)

    def get_stats(self) -> dict:
        return dict(self.stats)

    def make_decision(self, symbol: str, candles: list[Candle]):
        """تصمیم‌گیری بر اساس استراتژی اختصاصی نماد."""
        strategy = self.config.get(symbol)
        if strategy is None:
            return None

        if strategy == "simple":
            d = make_simple_decision(candles)
            return {
                "should_trade": d.should_trade,
                "action": d.action,
                "entry": d.entry_price,
                "tp": d.take_profit,
                "sl": d.stop_loss,
                "reason": f"[SIMPLE] {d.reason}",
                "strategy": "simple",
            }
        elif strategy == "bounce":
            d = make_bounce_decision(candles)
            return {
                "should_trade": d.should_trade,
                "action": d.action,
                "entry": d.entry_price,
                "tp": d.take_profit,
                "sl": d.stop_loss,
                "reason": f"[BOUNCE] {d.reason}",
                "strategy": "bounce",
            }
        return None


# Singleton
dispatcher = SmartDispatcher()
