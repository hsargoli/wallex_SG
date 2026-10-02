# 🏗 Architecture — Wallex Trading Platform

> معماری کامل سیستم، لایه‌ها، جریان داده، و تصمیمات طراحی.

**آخرین به‌روزرسانی:** ۲۰۲۶-۱۰-۰۲
**نسخه:** 1.0
**وضعیت:** فعال

---

## 📖 فهرست

1. [نگاه کلی](#نگاه-کلی)
2. [اصول طراحی](#اصول-طراحی)
3. [لایه‌های معماری](#لایههای-معماری)
4. [جریان داده](#جریان-داده)
5. [ساختار پوشه‌ها](#ساختار-پوشهها)
6. [Domain Layer](#domain-layer)
7. [Application Layer](#application-layer)
8. [Infrastructure Layer](#infrastructure-layer)
9. [Presentation Layer](#presentation-layer)
10. [Services Layer](#services-layer)
11. [معماری ربات‌ها](#معماری-رباتها)
12. [شبیه‌ساز](#شبیهساز)
13. [تصمیمات طراحی کلیدی](#تصمیمات-طراحی-کلیدی)
14. [محدودیت‌ها و بدهی فنی](#محدودیتها-و-بدهی-فنی)

---

## نگاه کلی

**Wallex Trading Platform** یک سیستم معاملات الگوریتمی روی صرافی والکس (wallex.ir) است که شامل:

- **Backend:** FastAPI + Python 3.12 + DDD Architecture
- **Frontend:** Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui
- **صفت کلیدی:** معماری تمیز، جداسازی لایه‌ها، تست‌پذیری بالا

### هدف اصلی

> ساخت یک پلتفرم بک‌تست و Paper Trading که کاربر بتونه استراتژی‌ها و ربات‌های مختلف رو روی داده‌ی واقعی صرافی والکس تست کنه و نتایج قابل اتکا بگیره.

---

## اصول طراحی

پروژه از **DDD (Domain-Driven Design)** و **Hexagonal Architecture** الهام گرفته:

| اصل | پیاده‌سازی |
|-----|-----------|
| **جداسازی لایه‌ها** | domain → application → infrastructure/presentation |
| **Dependency Inversion** | domain به هیچ‌چیز وابسته نیست |
| **Entities خالص** | `Candle`, `Market`, `Balance` بدون وابستگی |
| **Value Objects** | `Symbol` با اعتبارسنجی داخلی |
| **Ports & Adapters** | `ExchangePort` interface + Wallex adapter |
| **Use Cases** | یک کار مشخص در هر فایل |
| **تست‌پذیری** | Domain مستقل از DB/HTTP |

---

## لایه‌های معماری

```
┌──────────────────────────────────────────────────────────┐
│                    Presentation                          │
│         (FastAPI routers, dependencies, schemas)         │
└─────────────────────────┬────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────┐
│                    Application                           │
│         (Use Cases — هماهنگی بین لایه‌ها)                  │
└─────────────────────────┬────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────┐
│                     Domain                               │
│   (Entities, Value Objects, Ports, Exceptions)           │
│              ❌ صفر وابستگی خارجی                          │
└─────────────────────────▲────────────────────────────────┘
                          │
┌─────────────────────────┴────────────────────────────────┐
│                  Infrastructure                          │
│    (Wallex adapter, HTTP client, mapper, repository)     │
└──────────────────────────────────────────────────────────┘
```

### قاعده‌ی طلایی

> **جهت وابستگی همیشه به سمت Domain است.**
> Domain هیچ‌چیزی از لایه‌های دیگه import نمی‌کنه.

### استثنا: Services Layer

پروژه یک لایه‌ی `services/` هم دارد که **منطق کسب‌وکار پیچیده** (اندیکاتورها، استراتژی‌ها، شبیه‌ساز) را در خود جای می‌دهد. این لایه:

- از `domain/` استفاده می‌کند (entities)
- توسط `presentation/` صدا زده می‌شود
- معادل «Application Services» در DDD کلاسیک است

---

## جریان داده

### ۱. جریان معمولی (مثلاً دریافت قیمت لحظه‌ای)

```
User Browser
    │
    ▼ GET /v1/markets/BTCUSDT
┌─────────────────────────────────────┐
│ presentation/api/v1/markets.py      │
│  - هندل کردن request                │
│  - فراخوانی use case                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ application/use_cases/get_market.py │
│  - منطق کاربردی                     │
│  - فراخوانی port                    │
└──────────────┬──────────────────────┘
               │
               ▼ (از طریق interface)
┌─────────────────────────────────────┐
│ domain/ports/exchange.py            │
│  - interface (abstract)             │
└──────────────▲──────────────────────┘
               │ پیاده‌سازی
┌──────────────┴──────────────────────┐
│ infrastructure/exchange/wallex/     │
│  - client.py (HTTP)                 │
│  - mapper.py (DTO → Entity)         │
└──────────────┬──────────────────────┘
               │
               ▼
         Wallex API
     (api.wallex.ir/v1/...)
```

### ۲. جریان شبیه‌سازی (Backtest)

```
User Browser
    │
    ▼ POST /v1/simulation/run
      ?bot_slug=trend_follow
      &symbol=BTCUSDT
      &start_date=...
      &end_date=...
┌─────────────────────────────────────┐
│ presentation/api/v1/simulation.py   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ services/bot_simulator.py           │
│  - BotSimulator                     │
│  - انتخاب Adapter بر اساس slug     │
│  - حلقه‌ی زمانی                     │
│  - مدیریت position                  │
│  - کسر fee                          │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐   ┌──────────────────┐
│ Adapter     │   │ WallexMarketData │
│ (Decision)  │   │ (OHLCV)          │
└──────┬──────┘   └────────┬─────────┘
       │                   │
       ▼                   ▼
┌─────────────┐   ┌──────────────────┐
│ strategy.py │   │ api.wallex.ir    │
│ ربات خاص    │   │ /v1/udf/history  │
└─────────────┘   └──────────────────┘
```

---

## ساختار پوشه‌ها

### ریشه پروژه

```
wallex/
├── backend/              ← FastAPI + Python
├── frontend/             ← Next.js + TypeScript
├── docs/                 ← مستندات پروژه
│   ├── ARCHITECTURE.md   ← همین فایل
│   ├── SETUP.md          ← راهنمای راه‌اندازی
│   ├── API.md            ← مستندات API
│   ├── BOTS.md           ← راهنمای ربات‌ها
│   ├── ML_JOURNEY.md     ← سفر ML
│   └── reports/          ← گزارش‌های روزانه
├── .env                  ← متغیرهای محیطی (gitignored)
├── .env.example          ← نمونه
└── README.md             ← نقطه ورود
```

### Backend

```
backend/
├── app/
│   ├── main.py           ← Application Factory
│   ├── core/             ← تنظیمات، logging، exception
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exception_handlers.py
│   ├── domain/           ← ❤️ قلب سیستم
│   │   ├── entities/     ← Candle, Market, Balance
│   │   ├── models/       ← Budget, Profitability
│   │   ├── ports/        ← ExchangePort
│   │   ├── value_objects/ ← Symbol
│   │   └── exceptions.py
│   ├── application/
│   │   └── use_cases/    ← GetCandles, GetMarket, ...
│   ├── infrastructure/
│   │   ├── exchange/
│   │   │   └── wallex/   ← client.py, mapper.py
│   │   └── wallex_repo.py ← MarketDataRepository
│   ├── presentation/
│   │   └── api/
│   │       ├── deps.py   ← FastAPI dependencies
│   │       └── v1/       ← همه‌ی routerها
│   │           ├── router.py ← master router
│   │           ├── markets.py
│   │           ├── bots.py
│   │           ├── simulation.py
│   │           └── ...
│   └── services/         ← منطق کسب‌وکار پیچیده
│       ├── indicators.py ← RSI, EMA, MACD, ATR, ...
│       ├── bot_simulator.py
│       ├── simulator_engine.py
│       ├── bots/         ← ربات‌های معاملاتی
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── trend_follow/
│       │   ├── volatility_hunter/
│       │   ├── mean_revert/
│       │   ├── grid_bot/
│       │   └── smart_portfolio/
│       └── ... (۲۰+ فایل service)
├── scripts/
│   ├── tools/            ← ابزارهای روزمره
│   ├── ml/               ← ML فعال
│   └── archive/          ← آرشیو کامل
├── tests/
│   ├── unit/             ← تست‌های واحد
│   └── integration/      ← تست‌های integration
├── data/                 ← runtime data (models, state)
├── pyproject.toml        ← وابستگی‌ها + تنظیمات
└── README.md             ← راهنمای backend
```

### Frontend

```
frontend/
├── app/                  ← Next.js App Router
│   ├── layout.tsx        ← RTL + Vazirmatn
│   ├── page.tsx          ← Dashboard
│   ├── bots/             ← لیست و جزئیات ربات‌ها
│   ├── markets/          ← بازارها + چارت
│   ├── signals/          ← سیگنال‌ها
│   ├── scanner/          ← اسکنر بازار
│   ├── portfolio/        ← سبد دارایی
│   ├── wallet/           ← کیف پول
│   ├── budget/           ← بودجه
│   ├── profitability/    ← محاسبه‌گر سود
│   └── paper-trading/    ← شبیه‌ساز و Paper Trading
├── components/
│   ├── ui/               ← shadcn components
│   ├── charts/           ← نمودارها
│   ├── layout/           ← sidebar
│   ├── markets/
│   ├── signals/
│   └── portfolio/
├── lib/
│   ├── api.ts            ← کلاینت API
│   ├── queries.ts        ← React Query hooks
│   ├── format.ts         ← فرمترها
│   └── utils.ts          ← ابزارها
└── package.json
```

---

## Domain Layer

قلب سیستم. **صفر وابستگی به FastAPI، HTTP، DB.**

### Entities

| Entity | فایل | توضیح |
|--------|------|-------|
| `Candle` | `entities/candle.py` | کندل OHLCV با Decimal |
| `Market` | `entities/market.py` | بازار (symbol, base, quote, ...) |
| `Balance` | `entities/balance.py` | موجودی دارایی |

**مثال — Candle:**

```python
@dataclass(frozen=True, slots=True)
class Candle:
    time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
```

**نکات کلیدی:**
- `frozen=True` → immutable
- `Decimal` به‌جای `float` → دقت مالی
- `slots=True` → کارایی حافظه

### Value Objects

| VO | فایل | توضیح |
|----|------|-------|
| `Symbol` | `value_objects/symbol.py` | نماد با اعتبارسنجی |

### Ports (Interfaces)

| Port | فایل | توضیح |
|------|------|-------|
| `ExchangePort` | `ports/exchange.py` | interface صرافی |
| `MarketDataRepository` | `repository.py` | interface داده‌ی بازار |

### Exceptions

| Exception | HTTP Status |
|-----------|-------------|
| `DomainError` | 400 |
| `InvalidSymbolError` | 404 |
| `ExchangeAuthError` | 401 |
| `ExchangeRateLimitError` | 429 |
| `ExchangeUnavailableError` | 503 |

---

## Application Layer

### Use Cases

| Use Case | فایل | توضیح |
|----------|------|-------|
| `GetBalances` | `get_balances.py` | دریافت موجودی‌ها |
| `GetCandles` | `get_candles.py` | دریافت کندل‌ها |
| `GetMarket` | `get_market.py` | دریافت یک بازار |
| `GetMarkets` | `get_markets.py` | دریافت همه بازارها |
| `GetPortfolio` | `get_portfolio.py` | سبد دارایی |

**الگو:**

```python
class GetMarketUseCase:
    def __init__(self, exchange: ExchangePort):
        self.exchange = exchange

    async def execute(self, symbol: Symbol) -> Market:
        return await self.exchange.fetch_market(symbol)
```

---

## Infrastructure Layer

### Wallex Exchange Adapter

```
infrastructure/exchange/wallex/
├── client.py    ← HTTP client (httpx)
└── mapper.py    ← DTO → Entity
```

**نکات:**
- `httpx` برای async HTTP
- مدیریت retry و timeout
- mapper جدا برای تست‌پذیری

### Market Data Repository

```python
class WallexMarketData(MarketDataRepository):
    def get_candles(symbol, start, end, timeframe) -> List[Candle]:
        # اتصال به api.wallex.ir/v1/udf/history

    def get_prices(symbol, start, end) -> List[float]:
        # سازگاری عقب‌رو
```

**محدودیت API والکس:**
- `1h` فقط ~۷۲۰ کندل آخر (≈۳۰ روز)
- `1D` نامحدود
- تایم‌فریم‌های `1m/5m/15m/4h` معتبر نیستن (به `1m` یا `1h` fallback می‌کنن)

---

## Presentation Layer

### Routers

**۱۴ router** که توسط master router مدیریت می‌شن:

| Router | Prefix | توضیح |
|--------|--------|-------|
| `markets` | `/v1/markets` | بازارها، کندل‌ها، orderbook |
| `account` | `/v1/account` | موجودی، پورتفولیو |
| `bot` | `/v1/bot` | مدیریت بودجه |
| `bots` | `/v1/bots` | ربات‌های ثبت‌شده |
| `profitability` | `/v1/profitability` | محاسبه سود |
| `signals` | `/v1/signals` | سیگنال‌های معاملاتی |
| `scanner` | `/v1/scanner` | اسکنر بازار |
| `backtest` | `/v1/backtest` | بک‌تست |
| `scalping` | `/v1/scalping` | اسکالپینگ |
| `ml_bottom` | `/v1/ml/bottom` | ML کف‌شناسی |
| `paper_trading` | `/v1/paper` | Paper Trading v1 |
| `paper_v2` | `/v1/paper-v2` | Paper Trading v2 |
| `replay` | `/v1/replay` | Replay تاریخی |
| `simulation` | `/v1/simulation` | شبیه‌ساز ربات‌ها |

**الگوی master router:**

```python
# router.py
router = APIRouter(prefix="/v1")
router.include_router(markets.router)
router.include_router(bots.router)
# ... ۱۲ تای دیگه

# main.py
app.include_router(v1_router)
```

**نکته‌ی مهم:** این ساختار در تاریخ ۲۰۲۶-۱۰-۰۲ رفع شد — قبلاً `main.py` فقط ۳ router رو mount می‌کرد و ۱۱ تای دیگه پنهان بودن (۳۱ تست فیل).

---

## Services Layer

**۴۹ فایل** در `app/services/` که موضوعاً به چند دسته تقسیم می‌شن:

### ۱. تحلیل بازار (۸ فایل)
- `indicators.py` — RSI, EMA, MACD, ATR, Bollinger
- `bottom_detector.py` — کف‌شناسی
- `bounce_scalper.py` — استراتژی bounce
- `regime_detector.py` — تشخیص رژیم بازار
- `trend.py` — تحلیل روند
- `levels.py` — حمایت/مقاومت
- `volatility_predictor.py` — پیش‌بینی نوسان
- `anomaly_detector.py` — تشخیص ناهنجاری

### ۲. شبیه‌سازی و بک‌تست (۵ فایل)
- `bot_simulator.py` ⭐ — شبیه‌ساز اصلی ربات‌ها
- `simulator_engine.py` — شبیه‌ساز قدیمی (SimpleTrendStrategy)
- `backtest.py` — بک‌تست عمومی
- `historical_replay.py` — replay تاریخی
- `scalping_backtest.py` — بک‌تست اسکالپینگ

### ۳. معاملات (۶ فایل)
- `paper_trader.py` — Paper Trading v1
- `paper_trader_v2.py` — Paper Trading v2
- `grid_bot.py` — ربات گرید (قدیمی)
- `simple_bot.py` — ربات ساده
- `position_sizer.py` — مدیریت حجم
- `smart_dispatcher.py` — انتخاب استراتژی per-asset

### ۴. داده (۲ فایل)
- `candle_aggregator.py` — تجمیع کندل‌ها
- `indicators.py` — (قبلاً گفته شد)

### ۵. کسب‌وکار (۲ فایل)
- `budget_service.py` — مدیریت بودجه
- `profitability_service.py` — محاسبه سود

### ۶. ربات‌ها (پوشه `bots/`)
- `base.py` — اینترفیس BaseBot
- `registry.py` — ثبت ربات‌ها
- ۵ ربات فعال: `trend_follow`, `volatility_hunter`, `mean_revert`, `grid_bot`, `smart_portfolio`

---

## معماری ربات‌ها

### BaseBot Interface

```python
class BaseBot(ABC):
    @property
    def info(self) -> BotInfo: ...

    @property
    def status(self) -> BotStatus: ...

    async def start(self, exchange) -> dict: ...
    async def stop(self) -> dict: ...
    def reset(self) -> dict: ...
    def get_status(self) -> dict: ...
```

### ساختار هر ربات

```
bots/<bot_name>/
├── bot.py        ← کلاس اصلی (BaseBot)
├── config.py     ← تنظیمات (dataclass)
├── strategy.py   ← منطق تصمیم‌گیری (اختیاری)
└── __init__.py
```

### ربات‌های موجود

| ربات | slug | استراتژی | تایم‌فریم |
|------|------|----------|-----------|
| روندر | `trend_follow` | EMA Cross + ADX + Trailing Stop | 1h |
| نوسان‌گیر | `volatility_hunter` | Range Trading | 1h |
| کف‌زن | `mean_revert` | Bounce Scalper + Smart Dispatcher | 15m (→ 1h) |
| Grid | `grid_bot` | سطوح پله‌ای | 1h |
| Smart Portfolio | `smart_portfolio` | allocation چندنماد | — |

---

## شبیه‌ساز

### معماری Adapter Pattern

```
BotSimulator
    │
    ├── انتخاب Adapter بر اساس bot_slug
    │
    ▼
┌────────────────────────────┐
│ BaseBotAdapter             │
│  on_candle(candles, pos)   │
│      → {"action": "...",   │
│         "reason": "...",   │
│         "meta": {...}}     │
└─────────┬──────────────────┘
          │
    ┌─────┴─────┬──────────┬──────────┐
    ▼           ▼          ▼          ▼
TrendFollow Volatility MeanRevert  ...
Adapter     Hunter     Adapter
            Adapter
```

### قواعد پیاده‌سازی

1. **Decision on close[i]** — تصمیم روی کندل جاری
2. **Execution on open[i+1]** — اجرا روی کندل بعدی (رفع look-ahead bias)
3. **Fee** — از config ربات (`fee_pct`)
4. **Position sizing** — از config ربات (`position_size_pct`)
5. **SL/TP** — با high/low کندل، نه close
6. **Force close** — بستن اجباری در پایان شبیه‌سازی

### فایل‌های کلیدی

- `bot_simulator.py` — موتور اصلی
- `presentation/api/v1/simulation.py` — endpoint
- `infrastructure/wallex_repo.py` — دریافت OHLCV

### خروجی

```json
{
  "status": "success",
  "symbol": "BTCUSDT",
  "bot_slug": "trend_follow",
  "timeframe": "1h",
  "fee_pct": 0.2,
  "position_size_pct": 30.0,
  "prices_count": 695,
  "trades": ["..."],
  "pnl_report": {
    "initial_balance": 1000.0,
    "final_balance": 1039.4,
    "total_pnl": 39.4,
    "pnl_pct": 3.94,
    "total_trades": 5,
    "wins": 4,
    "losses": 1,
    "win_rate": 80.0
  }
}
```

---

## تصمیمات طراحی کلیدی

### ۱. چرا DDD؟

- **تست‌پذیری:** domain رو می‌تونی بدون DB تست کنی
- **مقیاس‌پذیری:** هر لایه مستقل قابل جایگزینی
- **خوانایی:** هر کس می‌دونه کد کجا قرار می‌گیره

### ۲. چرا `Decimal` به‌جای `float`؟

```python
# بد:
0.1 + 0.2  # = 0.30000000000000004

# خوب:
Decimal("0.1") + Decimal("0.2")  # = Decimal('0.3')
```

برای پول و قیمت، دقت حیاتی است.

### ۳. چرا Adapter Pattern برای ربات‌ها؟

- اضافه کردن ربات جدید → فقط یه فایل Adapter
- هر ربات می‌تونه منطق مستقل داشته باشه
- شبیه‌ساز از جزئیات ربات بی‌خبره

### ۴. چرا force-close در پایان؟

بک‌تست باید سود/زیان **لحظه‌ای** رو محاسبه کنه. اگه پوزیشن باز بمونه، PnL ناقصه.

### ۵. چرا master router؟

قبلاً ۱۱ router پنهان بودن چون `main.py` فقط ۳ تا رو include می‌کرد. الان تنها نقطه‌ی مدیریت `router.py` هست.

---

## محدودیت‌ها و بدهی فنی

### محدودیت‌های API والکس

| تایم‌فریم | محدودیت |
|-----------|---------|
| `1h` | فقط ~۷۲۰ کندل آخر (≈۳۰ روز) |
| `1D` | نامحدود |
| `15m`, `5m`, `30m`, `4h` | معتبر نیستن |

### بدهی فنی فعلی

1. **کش دیتابیس نداریم** — هر بار از API می‌گیریم
2. **`services/` شلوغه** — ۲۷ فایل در روت، نیاز به گروه‌بندی
3. **بدون CI/CD** — تست‌ها دستی اجرا می‌شن
4. **بدون Alembic** — state تو JSON فایل ذخیره میشه
5. **تست‌های integration ناقص** — فقط ۳ فایل

### بهبودهای پیشنهادی

- [ ] کش کندل‌ها در SQLite/Postgres
- [ ] گروه‌بندی `services/` (تحلیل/معاملات/داده)
- [ ] اضافه کردن GitHub Actions / CI
- [ ] WebSocket برای قیمت لحظه‌ای
- [ ] Grafana / Prometheus برای monitoring

---

## لینک‌های مرتبط

- [SETUP.md](./SETUP.md) — راه‌اندازی
- [API.md](./API.md) — مستندات API
- [BOTS.md](./BOTS.md) — راهنمای ربات‌ها
- [ML_JOURNEY.md](./ML_JOURNEY.md) — سفر ML
- [reports/](./reports/) — گزارش‌های روزانه

---

**پایان مستند — نسخه ۱.۰**
