🤖 راهنمای ربات‌ها — Wallex

نسخه: ۲.۰
آخرین به‌روزرسانی: 2026-10-06
📖 فهرست

    نگاه کلی

    معماری ربات‌ها

    BaseBot Interface

    ربات‌های موجود

    Adapter Pattern

    اضافه کردن ربات جدید

    مقایسه ربات‌ها

    لینک‌های مرتبط

نگاه کلی

پلتفرم والکس ۶ ربات معاملاتی داره که هر کدوم استراتژی مستقل خودش رو داره.
هر ربات از یه interface مشترک (BaseBot) پیروی می‌کنه و از طریق Registry قابل کشف هست.
Registry

`python
from app.services.bots.registry import get_all_bots, get_bot

bots = get_all_bots() # لیست همه
bot = get_bot("trend_follow") # یه ربات خاص
`
معماری ربات‌ها
ساختار پوشه‌ها

`text
backend/app/services/bots/
├── base.py ← BaseBot, BotInfo, BotStatus
├── registry.py ← ثبت و کشف ربات‌ها
├── trend_follow/ ← ربات ۱
│ ├── config.py
│ ├── bot.py
│ └── strategy.py
├── volatility_hunter/ ← ربات ۲
├── volatility_hunter_v2/ ← ربات ۳
├── mean_revert/ ← ربات ۴
├── grid_bot/ ← ربات ۵
└── smart_portfolio/ ← ربات ۶
`
چرخه‌ی حیات یک ربات

`text
IDLE → start() → RUNNING → stop() → STOPPED
↓
reset() → IDLE
`
BaseBot Interface

هر ربات باید این interface رو پیاده‌سازی کنه:

`python
class BaseBot(ABC):
@property
def info(self) -> BotInfo: ...

@property
def status(self) -> BotStatus: ...

async def start(self, exchange) -> dict: ...

async def stop(self) -> dict: ...

def reset(self) -> dict: ...

def make_decision(self, symbol, candles) -> dict | None: ...
`
BotInfo

`python
@dataclass
class BotInfo:
slug: str # شناسه یکتا
name: str # نام فارسی
name_en: str # نام انگلیسی
version: str # نسخه
description: str # توضیح
tags: list[str] # تگ‌ها
capabilities: list[str] # paper, live, backtest
`
ربات‌های موجود
#	ربات	slug	نوع	وضعیت	مستند
| ۱ | روندر | `trend_follow` | Trend Following | ✅ آماده | [مشاهده](./bots/trend_follow.md) |
| ۲ | نوسان‌گیر | `volatility_hunter` | Range Trading | ✅ آماده | [مشاهده](./bots/volatility_hunter.md) |
| ۳ | نوسان‌گیر v2 | `volatility_hunter_v2` | Range Trading | ✅ آماده | [مشاهده](./bots/volatility_hunter_v2.md) |
| ۴ | کف‌زن | `mean_revert` | Mean Reversion | ⚠️ آزمایشی | [مشاهده](./bots/mean_revert.md) |
| ۵ | شبکه‌ای | `grid_bot` | Grid Trading | ⚠️ نیمه‌کاره | [مشاهده](./bots/grid_bot.md) |
| ۶ | پورتفوی هوشمند | `smart_portfolio` | Meta-bot | ⚠️ آزمایشی | [مشاهده](./bots/smart_portfolio.md) |

برای جزئیات هر ربات، روی لینک «مشاهده» کلیک کن.
Adapter Pattern در شبیه‌ساز
چرا Adapter؟

هر ربات یه interface داره، ولی شبیه‌ساز نیاز به interface خاص خودش داره.
Adapter این واسطه رو فراهم می‌کنه.
معماری

`text
Simulator → Adapter → Bot
`
اینترفیس Adapter

`python
class BotAdapter(ABC):
def on_candle(self, candle: Candle) -> Signal | None: ...
def get_state(self) -> dict: ...
`
Adapterهای موجود
ربات	Adapter	وضعیت
trend_follow	✅	آماده
volatility_hunter	✅	آماده
volatility_hunter_v2	✅	آماده
mean_revert	✅	آماده
grid_bot	❌	نیاز به شبیه‌ساز چندپوزیشنی
smart_portfolio	❌	multi-asset
اضافه کردن ربات جدید
مرحله ۱: ساخت پوشه

`bash
mkdir -p backend/app/services/bots/my_bot
`
مرحله ۲: Config

`python
backend/app/services/bots/my_bot/config.py

from dataclasses import dataclass

@dataclass(slots=True)
class MyBotConfig:
timeframe: str = "1h"
position_size_pct: float = 30.0
`
مرحله ۳: Bot

`python
backend/app/services/bots/my_bot/bot.py

from app.services.bots.base import BaseBot, BotInfo, BotStatus

class MyBot(BaseBot):
@property
def info(self) -> BotInfo:
return BotInfo(
slug="my_bot",
name="ربات من",
name_en="My Bot",
version="0.1.0",
description="...",
tags=["..."],
capabilities=["paper", "backtest"],
)
... پیاده‌سازی متدها

`
مرحله ۴: Strategy (اختیاری)

`python
backend/app/services/bots/my_bot/strategy.py

def evaluate_entry(candles, config) -> Signal | None:
...
`
مرحله ۵: ثبت در Registry

`python
backend/app/services/bots/registry.py

from app.services.bots.my_bot.bot import MyBot

BOTS = {
...
"my_bot": MyBot,
}
`
مرحله ۶: Adapter برای شبیه‌ساز

`python
backend/app/services/simulator/adapters/my_bot.py

from app.services.simulator.adapters.base import BotAdapter

class MyBotAdapter(BotAdapter):
...
`
مرحله ۷: تست

`bash
cd backend
uv run pytest tests/unit/bots/test_my_bot.py
`
مقایسه ربات‌ها
ربات	نوع	تایم‌فریم	بهترین بازار	WR تست
trend_follow	Trend	1h	رونددار	32%
volatility_hunter	Range	1h	رنج	—
volatility_hunter_v2	Range	1h	رنج	40.6%
mean_revert	Mean Rev	15m→1h	نوسانی	—
grid_bot	Grid	1h	رنج پایدار	90.4%
smart_portfolio	Meta	1h	همه	—

جزئیات بیشتر: docs/bots/
لینک‌های مرتبط

    docs/bots/ — مستندات تفصیلی هر ربات

    ARCHITECTURE.md — معماری کلان

    API.md — مستندات endpointها

    GETTING_STARTED.md — شروع کار

    BOTS.md.bak — نسخه قبلی (بکاپ)

پایان مستند — نسخه ۲.۰
