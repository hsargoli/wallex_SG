"""تنظیمات Smart Portfolio."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class BotAllocation:
    """تخصیص یک ربات در یک رژیم."""

    bot_slug: str
    weight: float  # 0.0 - 1.0
    confidence_min: int = 0  # حداقل اطمینان برای فعال شدن


@dataclass(slots=True)
class SmartPortfolioConfig:
    """تنظیمات پورتفوی هوشمند."""

    total_capital: float = 300_000.0
    timeframe: str = "1h"
    max_concurrent_bots: int = 2

    # نقشه‌ی رژیم → ربات‌ها
    # در هر رژیم، لیست ربات‌ها با وزن
    regime_map: dict = field(
        default_factory=lambda: {
            "trending_up": [
                BotAllocation("trend_follow", 1.0),
            ],
            "ranging": [
                BotAllocation("mean_revert", 0.6),
                BotAllocation("grid_bot", 0.4),
            ],
            "choppy": [
                BotAllocation("volatility_hunter", 1.0),
            ],
            "trending_down": [
                # در روند نزولی، هیچ رباتی فعال نیست
            ],
        }
    )

    # اگه رژیم نامشخص بود
    default_allocation: list = field(
        default_factory=lambda: [
            BotAllocation("mean_revert", 0.5),
            BotAllocation("volatility_hunter", 0.5),
        ]
    )

    # Rebalance
    rebalance_interval_min: int = 60  # هر ۶۰ دقیقه چک رژیم
