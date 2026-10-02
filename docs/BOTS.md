# 🤖 Bots Guide — Wallex Trading Platform

> راهنمای کامل ربات‌های معاملاتی: استراتژی، معماری، و نحوه اضافه کردن ربات جدید.

**آخرین به‌روزرسانی:** ۲۰۲۶-۱۰-۰۲
**نسخه:** 1.0
**تعداد ربات‌ها:** ۵

---

## 📖 فهرست

1. [نگاه کلی](#نگاه-کلی)
2. [معماری ربات‌ها](#معماری-رباتها)
3. [BaseBot Interface](#basebot-interface)
4. [ربات‌های موجود](#رباتهای-موجود)
   - [روندر (Trend Follow)](#روندر-trend-follow)
   - [نوسان‌گیر (Volatility Hunter)](#نوسانگیر-volatility-hunter)
   - [کف‌زن (Mean Revert)](#کفزن-mean-revert)
   - [Grid Bot](#grid-bot)
   - [Smart Portfolio](#smart-portfolio)
5. [Adapter Pattern در شبیه‌ساز](#adapter-pattern-در-شبیهساز)
6. [اضافه کردن ربات جدید](#اضافه-کردن-ربات-جدید)
7. [مقایسه ربات‌ها](#مقایسه-رباتها)
8. [نتایج شبیه‌سازی](#نتایج-شبیهسازی)
9. [لینک‌های مرتبط](#لینکهای-مرتبط)

---

## نگاه کلی

پلتفرم Wallex شامل **۵ ربات معاملاتی** است که هرکدام استراتژی خاص خود را دارند. هر ربات:

- **مستقل است** — منطق و پارامترهای جداگانه
- **قابل تست است** — هم در شبیه‌سازی، هم Paper Trading، هم Live
- **Registry-based** — با slug یکتا شناخته می‌شود
- **Adapter دارد** — برای استفاده در شبیه‌ساز

### Registry

تمام ربات‌ها در `bot_registry` ثبت می‌شن:

```python
from app.services.bots import bot_registry

# لیست همه
for bot in bot_registry.list_all():
    print(bot.info.slug)

# پیدا کردن با slug
bot = bot_registry.get("trend_follow")
```

---

## معماری ربات‌ها

### ساختار پوشه‌ها

```
app/services/bots/
├── base.py              ← اینترفیس BaseBot
├── registry.py          ← ثبت و مدیریت ربات‌ها
├── trend_follow/
│   ├── bot.py
│   ├── config.py
│   └── strategy.py
├── volatility_hunter/
│   ├── bot.py
│   ├── config.py
│   └── strategy.py
├── mean_revert/
│   ├── bot.py
│   └── config.py
├── grid_bot/
│   ├── bot.py
│   ├── config.py
│   └── strategy.py
└── smart_portfolio/
    ├── bot.py
    ├── config.py
    └── allocator.py
```

### چرخه‌ی حیات یک ربات

```
IDLE ──start()──> RUNNING ──stop()──> STOPPED
  ▲                  │                    │
  └────reset()───────┴────────────────────┘
```

| وضعیت | توضیح |
|-------|-------|
| `IDLE` | آماده، ولی شروع نشده |
| `RUNNING` | در حال اجرا |
| `STOPPED` | متوقف شده (state حفظ میشه) |
| `ERROR` | خطا |

---

## BaseBot Interface

هر ربات باید از `BaseBot` ارث‌بری کنه:

```python
from abc import ABC, abstractmethod
from app.services.bots.base import BaseBot, BotInfo, BotStatus


class BaseBot(ABC):
    @property
    @abstractmethod
    def info(self) -> BotInfo:
        """شناسنامه ربات."""

    @property
    @abstractmethod
    def status(self) -> BotStatus:
        """وضعیت فعلی."""

    @abstractmethod
    async def start(self, exchange) -> dict:
        """شروع ربات."""

    @abstractmethod
    async def stop(self) -> dict:
        """توقف ربات."""

    @abstractmethod
    def reset(self) -> dict:
        """ریست کامل state."""

    @abstractmethod
    def get_status(self) -> dict:
        """وضعیت کامل."""
```

### BotInfo

```python
@dataclass(slots=True)
class BotInfo:
    slug: str                       # "trend_follow"
    name: str                       # "روندر"
    name_en: str                    # "Trend Follow Bot"
    version: str                    # "0.1.0"
    description: str                # توضیحات
    tags: list[str]                 # ["trend_following", "momentum"]
    capabilities: list[str]         # ["paper", "live", "backtest"]
    author: str = "ROSHD_SARV"
```

---

## ربات‌های موجود

### روندر (Trend Follow)

**slug:** `trend_follow`

**استراتژی:** دنبال کردن روند صعودی با EMA Cross + ADX + Trailing Stop

**پارامترها:**

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `timeframe` | 1h | تایم‌فریم |
| `ema_fast` | 20 | EMA سریع |
| `ema_slow` | 50 | EMA کند |
| `adx_period` | 14 | دوره ADX |
| `adx_threshold` | 20.0 | حداقل ADX |
| `sl_atr_mult` | 3.0 | ضریب ATR برای SL |
| `trail_atr_mult` | 2.5 | ضریب ATR برای trailing |
| `max_duration_candles` | 168 | حداکثر ۷ روز |
| `position_size_pct` | 30.0 | ۳۰٪ سرمایه |
| `fee_pct` | 0.2 | کارمزد |

**منطق ورود:**
1. **Golden Cross** — EMA سریع از پایین EMA کند رو قطع کنه
2. **یا Continuation** — EMA aligned + ADX > 20 (ادامه‌ی روند)
3. فیلتر حجم: حجم کندل ≥ میانگین ۲۰ کندل

**منطق خروج:**
- `trailing_sl` — SL متحرک خورده
- `initial_sl` — SL اولیه خورده
- `reverse_cross` — کراس نزولی
- `timeout` — ۱۶۸ کندل گذشت

**تایم‌فریم:** 1h (پشتیبانی‌شده توسط والکس)

**کاربرد:** بازارهای روند‌دار

---

### نوسان‌گیر (Volatility Hunter)

**slug:** `volatility_hunter`

**استراتژی:** Range Trading — خرید در کف range، فروش در سقف

**پارامترها:**

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `timeframe` | 1h | تایم‌فریم |
| `lookback_candles` | 48 | دوره تشخیص range |
| `min_range_pct` | 3.0 | حداقل range |
| `max_range_pct` | 12.0 | حداکثر range |
| `min_atr_pct` | 0.35 | حداقل ATR% |
| `buy_zone_pct` | 15.0 | ناحیه خرید |
| `stop_loss_pct` | 2.0 | SL |
| `take_profit_pct` | 4.0 | TP |
| `position_size_pct` | 30.0 | ۳۰٪ سرمایه |

**منطق ورود:**
1. تشخیص range معتبر (نه روند)
2. ورود در ۱۵٪ پایینی range

**منطق خروج:**
- `stop_loss` — SL
- `take_profit` — TP
- `breakout_up` / `breakout_down` — شکست range

**تایم‌فریم:** 1h

**کاربرد:** بازارهای رنج / نوسانی

**عملکرد تست:** +4.01% در ETH (۳۰ روز) — بهترین ربات عمومی

---

### کف‌زن (Mean Revert)

**slug:** `mean_revert`

**استراتژی:** خرید در کف و فروش در سود کوچک

**⚠️ هشدار:** این ربات برای تایم‌فریم **15m** طراحی شده، ولی والکس این تایم‌فریم رو پشتیبانی نمی‌کنه. ما مجبوریم روی **1h** اجرا کنیم. نتایج ممکنه دقیق نباشن.

**پارامترها:**

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `timeframe` | 15m → 1h | تایم‌فریم (اجباری) |
| `warmup_candles` | 100 | کندل‌های warmup |
| `max_duration_candles` | 24 | timeout (تست) |
| `SL` | 3.0% | (تنظیم‌شده برای 1h) |
| `TP` | 4.0% | (تنظیم‌شده برای 1h) |

**منطق:**
1. **Smart Dispatcher** — انتخاب استراتژی per-asset از `strategy_config.json`
2. Fallback: **Bounce Scalper**
3. تشخیص کف با score ≥ 6
4. SL/TP تنظیم‌شده برای 1h

**تایم‌فریم:** 15m (اصلی) → 1h (اجباری)

**وضعیت:** experimental (با هشدار در UI)

---

### Grid Bot

**slug:** `grid_bot`

**استراتژی:** خرید و فروش پله‌ای در سطوح مختلف

**پارامترها:**

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `n_buy_levels` | 3 | سطوح خرید |
| `n_sell_levels` | 3 | سطوح فروش |
| `grid_spacing_atr` | 0.6 | فاصله سطوح (×ATR) |
| `cash_per_level_pct` | 25.0 | سرمایه هر سطح |
| `adx_max` | 25.0 | فقط در رنج |
| `reset_after_hours` | 72 | ریست هر ۳ روز |

**منطق:**
1. فقط در بازار رنج فعال میشه (ADX < 25)
2. N سطح خرید زیر قیمت + N سطح فروش بالا
3. هر سطح پر شد → سود کوچیک در سطح بعدی
4. Reset هر ۷۲ ساعت

**وضعیت:** ثبت‌شده ولی Adapter شبیه‌ساز نداره (نیاز به شبیه‌ساز چندپوزیشنی)

---

### Smart Portfolio

**slug:** `smart_portfolio`

**استراتژی:** تخصیص سرمایه بین چند نماد

**نوع:** Multi-asset (نه تک‌نماد)

**کاربرد:** مدیریت سبد، نه ترید تک‌نماد

**وضعیت:** برای شبیه‌سازی تک‌نماد مناسب نیست

---

## Adapter Pattern در شبیه‌ساز

### چرا Adapter؟

شبیه‌ساز `BotSimulator` باید با **هر رباتی** کار کنه، ولی هر ربات منطق خودش رو داره. Adapter این ناسازگاری رو حل می‌کنه.

### معماری

```
BotSimulator
    │
    ├── انتخاب Adapter بر اساس bot_slug
    │
    ▼
┌────────────────────────────────┐
│  BaseBotAdapter                │
│  on_candle(candles, position)  │
│    → {action, reason, meta}    │
└────────────┬───────────────────┘
             │
    ┌────────┴─────────┬──────────────┐
    ▼                  ▼              ▼
TrendFollow       Volatility      MeanRevert
Adapter           HunterAdapter   Adapter
```

### اینترفیس Adapter

```python
class BaseBotAdapter:
    slug: str = ""
    timeframe: str = "1D"

    @property
    def fee_pct(self) -> float:
        return float(getattr(self.config, "fee_pct", 0.2))

    @property
    def position_size_pct(self) -> float:
        return float(getattr(self.config, "position_size_pct", 100.0))

    def on_candle(self, candles, position) -> dict:
        """
        خروجی:
          {"action": "hold"}
          {"action": "enter", "reason": str, "meta": {...}}
          {"action": "exit", "reason": str}
          {"action": "update", "meta": {...}}
        """
```

### Adapterهای موجود

| Adapter | slug | تایم‌فریم | وضعیت |
|---------|------|-----------|-------|
| `TrendFollowAdapter` | trend_follow | 1h | ✅ فعال |
| `VolatilityHunterAdapter` | volatility_hunter | 1h | ✅ فعال |
| `MeanRevertAdapter` | mean_revert | 1h | ⚠️ experimental |

---

## اضافه کردن ربات جدید

### مرحله ۱: ساخت پوشه

```bash
cd ~/wallex/backend
mkdir -p app/services/bots/my_bot
touch app/services/bots/my_bot/__init__.py
```

### مرحله ۲: Config

```python
# app/services/bots/my_bot/config.py
from dataclasses import dataclass


@dataclass(slots=True)
class MyBotConfig:
    timeframe: str = "1h"
    fee_pct: float = 0.2
    position_size_pct: float = 30.0
    # پارامترهای اختصاصی
    my_param: float = 10.0
```

### مرحله ۳: Bot

```python
# app/services/bots/my_bot/bot.py
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.my_bot.config import MyBotConfig


class MyBot(BaseBot):
    def __init__(self, config: MyBotConfig | None = None):
        self.config = config or MyBotConfig()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="my_bot",
            name="ربات من",
            name_en="My Bot",
            version="0.1.0",
            description="توضیح کوتاه",
            tags=["custom", "test"],
            capabilities=["paper", "backtest"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        self._status = BotStatus.RUNNING
        return {"status": "started", "bot": "my_bot"}

    async def stop(self) -> dict:
        self._status = BotStatus.STOPPED
        return {"status": "stopped"}

    def reset(self) -> dict:
        self._status = BotStatus.IDLE
        return {"status": "reset"}

    def get_status(self) -> dict:
        return {"is_running": self._status == BotStatus.RUNNING}
```

### مرحله ۴: Strategy (اختیاری)

```python
# app/services/bots/my_bot/strategy.py
from app.domain.entities.candle import Candle


def should_enter(candles: list[Candle], config: MyBotConfig) -> bool:
    # منطق ورود
    return False


def should_exit(candles: list[Candle], entry_price: float, config: MyBotConfig) -> bool:
    # منطق خروج
    return False
```

### مرحله ۵: ثبت در Registry

```python
# app/services/bots/__init__.py
from app.services.bots.my_bot import MyBot
from app.services.bots.registry import bot_registry


def _register_all():
    # ...
    if "my_bot" not in bot_registry:
        bot_registry.register(MyBot())
```

### مرحله ۶: Adapter برای شبیه‌ساز

```python
# app/services/bot_simulator.py
class MyBotAdapter(BaseBotAdapter):
    slug = "my_bot"

    def __init__(self):
        from app.services.bots.my_bot.config import MyBotConfig
        self.config = MyBotConfig()
        self.timeframe = self.config.timeframe

    def on_candle(self, candles, position):
        from app.services.bots.my_bot.strategy import should_enter, should_exit

        if position is None:
            if should_enter(candles, self.config):
                return {
                    "action": "enter",
                    "reason": "signal",
                    "meta": {"sl": ..., "tp": ...},
                }
            return {"action": "hold"}

        if should_exit(candles, position["entry_price"], self.config):
            return {"action": "exit", "reason": "signal"}

        return {"action": "hold"}


ADAPTERS = {
    # ...
    "my_bot": MyBotAdapter,
}
```

### مرحله ۷: تست

```bash
# چک ثبت
uv run python -c "
from app.services.bots import bot_registry
print([b.info.slug for b in bot_registry.list_all()])
"

# چک Adapter
uv run python -c "
from app.services.bot_simulator import list_simulatable_bots
print(list_simulatable_bots())
"

# شبیه‌سازی
curl -X POST "http://127.0.0.1:8000/v1/simulation/run?start_date=2026-09-02&end_date=2026-10-02&bot_slug=my_bot"
```

---

## مقایسه ربات‌ها

| ربات | تایم‌فریم | استراتژی | SL/TP | وضعیت |
|------|-----------|----------|-------|-------|
| روندر | 1h | Trend Follow | Trailing + ATR | ✅ آماده |
| نوسان‌گیر | 1h | Range Trading | 2% / 4% | ✅ آماده |
| کف‌زن | 1h (→ 15m) | Mean Revert | 3% / 4% | ⚠️ experimental |
| Grid | 1h | Grid Trading | ATR-based | 🔜 بزودی |
| Smart Portfolio | — | Multi-asset | — | 🔜 بزودی |

---

## نتایج شبیه‌سازی

### ETHUSDT (۳۰ روز، 1h، 1000 USDT)

| رتبه | ربات | معاملات | WR | PnL |
|------|------|---------|-----|-----|
| 🥇 | نوسان‌گیر | 5 | 80.0% | **+4.01%** |
| 🥈 | کف‌زن | 13 | 38.5% | -0.74% |
| 🥉 | روندر | 14 | 21.4% | -1.81% |

### مشاهده کلی (۷ رمزارز)

- **نوسان‌گیر:** ۶ از ۷ رمزارز مثبت — بهترین عملکرد کلی
- **روندر:** مناسب روند (SOL, XRP)، ضعیف در رنج (BTC, ETH)
- **کف‌زن:** ناسازگاری تایم‌فریم — با هشدار نمایش داده می‌شود

---

## لینک‌های مرتبط

- [ARCHITECTURE.md](./ARCHITECTURE.md) — معماری کلی
- [SETUP.md](./SETUP.md) — راه‌اندازی
- [API.md](./API.md) — مستندات API
- [ML_JOURNEY.md](./ML_JOURNEY.md) — سفر ML

---

**پایان مستند — نسخه ۱.۰**
