# 🔌 API Reference — Wallex Trading Platform

> مستندات کامل API بک‌اند (۴۴ endpoint در ۱۵ گروه).

**آخرین به‌روزرسانی:** ۲۰۲۶-۱۰-۰۲
**نسخه API:** v1
**Base URL:** `http://127.0.0.1:8000`

---

## 📖 فهرست

1. [نگاه کلی](#نگاه-کلی)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limits](#rate-limits)
5. [Accounts](#accounts)
6. [Markets](#markets)
7. [Signals](#signals)
8. [Scanner](#scanner)
9. [Bots](#bots)
10. [Bot Management](#bot-management)
11. [Profitability](#profitability)
12. [Simulation](#simulation)
13. [Paper Trading v1](#paper-trading-v1)
14. [Paper Trading v2](#paper-trading-v2)
15. [Historical Replay](#historical-replay)
16. [Backtest](#backtest)
17. [Scalping](#scalping)
18. [ML Bottom](#ml-bottom)
19. [لینک‌های مرتبط](#لینکهای-مرتبط)

---

## نگاه کلی

### Base URL

```
http://127.0.0.1:8000
```

### نسخه‌بندی

همه‌ی endpointها با `/v1/` شروع می‌شن:

```
GET  /v1/markets
GET  /v1/bots
POST /v1/simulation/run
```

### فرمت درخواست

- **Content-Type:** `application/json`
- **Query Params:** برای فیلترها و pagination
- **Body:** برای عملیات POST/PUT

### مستندات تعاملی

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

---

## Authentication

**✅ وضعیت فعلی:** API کاملاً با **JWT (JSON Web Token)** محافظت می‌شود.
برای دسترسی به Endpointهای محافظت‌شده، باید توکن را در هدر `Authorization: Bearer <token>` ارسال کنید.

### 🔐 Auth Endpoints
- `POST /v1/auth/register` — ثبت‌نام کاربر.
- `POST /v1/auth/login` — ورود و دریافت JWT (با محدودیت ۵ بار در دقیقه).
- `POST /v1/auth/forgot-password` — ارسال لینک بازیابی رمز (با محدودیت ۳ بار در دقیقه).
- `POST /v1/auth/reset-password` — تغییر رمز با استفاده از توکن ایمیل.
- `POST /v1/auth/verify-email` — تایید آدرس ایمیل.

### 🏦 Wallex Endpoints
- `POST /v1/user/wallex/connect` — اتصال توکن View (برای دیدن موجودی).
- `POST /v1/user/wallex/connect-trade` — اتصال توکن Trade (برای ثبت سفارش).
- `DELETE /v1/user/wallex/disconnect-trade` — قطع اتصال توکن معاملات.


**نکته امنیتی:** API Key والکس در `.env` بک‌اند نگهداری میشه، نه در requestهای کاربر.

---

## Error Handling

پروژه از **RFC-7807 (Problem Details)** استفاده می‌کنه:

```json
{
  "type": "https://wallex.local/errors/invalid-symbol",
  "title": "Invalid Symbol",
  "status": 404,
  "detail": "Symbol 'XYZUSDT' not found",
  "instance": "/v1/markets/XYZUSDT"
}
```

### جدول خطاها

| HTTP Status | Exception | توضیح |
|-------------|-----------|-------|
| **400** | `DomainError` | خطای عمومی منطق کسب‌وکار |
| **401** | `ExchangeAuthError` | مشکل احراز هویت با والکس |
| **404** | `InvalidSymbolError` | نماد پیدا نشد |
| **422** | `ValidationError` | خطای اعتبارسنجی Pydantic |
| **429** | `ExchangeRateLimitError` | محدودیت نرخ والکس |
| **503** | `ExchangeUnavailableError` | والکس در دسترس نیست |

---

## Rate Limits

**API خودمان:** بدون محدودیت
**API والکس (خارجی):**

| محدودیت | مقدار |
|---------|-------|
| Request per second | ~10 |
| Burst | ~20 |

**توصیه:** برای درخواست‌های دسته‌ای، از cache استفاده کن (`CACHE_TTL_SECONDS=5`).

---

## Accounts

مدیریت حساب، موجودی‌ها و پورتفولیو.

### `GET /v1/account/balances`

دریافت همه‌ی موجودی‌های حساب.

**Response:**
```json
{
  "count": 3,
  "items": [
    {
      "asset": "USDT",
      "available": "1500.50",
      "locked": "0.00",
      "total": "1500.50",
      "fa_name": "تتر",
      "en_name": "Tether"
    }
  ]
}
```

### `GET /v1/account/key-assets`

دریافت دارایی‌های کلیدی (خلاصه).

### `GET /v1/account/portfolio`

پورتفولیو کامل با ارزش‌گذاری.

**Response:**
```json
{
  "count": 3,
  "total_value_tmn_bid": "45000000",
  "total_value_usdt_bid": "1500",
  "usdt_tmn_rate": "91000",
  "items": [...]
}
```

---

## Markets

اطلاعات بازارها، کندل‌ها و orderbook.

### `GET /v1/markets`

لیست همه‌ی بازارهای فعال.

**Query Params:**

| پارامتر | نوع | توضیح |
|---------|-----|-------|
| `quote` | string | فیلتر بر اساس quote (`USDT`, `TMN`) |

**Response:**
```json
{
  "count": 120,
  "items": [
    {
      "symbol": "BTCUSDT",
      "base_asset": "BTC",
      "quote_asset": "USDT",
      "last_price": "122379.98",
      "fa_name": "بیت‌کوین",
      "en_name": "Bitcoin"
    }
  ]
}
```

### `GET /v1/markets/{symbol}`

اطلاعات یک بازار خاص.

**مثال:**
```bash
curl "http://127.0.0.1:8000/v1/markets/BTCUSDT"
```

### `GET /v1/markets/orderbook/{symbol}`

Order book یک بازار.

**Query Params:**

| پارامتر | نوع | پیش‌فرض | توضیح |
|---------|-----|---------|-------|
| `depth` | int | 20 | تعداد سطوح |

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "best_bid": "122379.98",
  "best_ask": "122380.00",
  "spread": "0.02",
  "spread_pct": "0.00002",
  "bids": [{"price": "...", "quantity": "...", "sum": "..."}],
  "asks": [...]
}
```

### `GET /v1/markets/candles/{symbol}`

کندل‌های OHLCV یک نماد.

**Query Params:**

| پارامتر | نوع | مقادیر مجاز | پیش‌فرض |
|---------|-----|-------------|---------|
| `tf` | string | `1h`, `1D` | `1h` |
| `limit` | int | 1-3500 | 500 |

**مثال:**
```bash
curl "http://127.0.0.1:8000/v1/markets/candles/BTCUSDT?tf=1h&limit=100"
```

**⚠️ محدودیت API والکس:**
- `1h` → فقط ~۷۲۰ کندل آخر (≈۳۰ روز)
- `1D` → نامحدود
- سایر تایم‌فریم‌ها پشتیبانی نمی‌شن

---

## Signals

سیگنال‌های معاملاتی و اندیکاتورها.

### `GET /v1/signals/{symbol}`

سیگنال معاملاتی یک نماد.

**Query Params:** `tf` (پیش‌فرض: `1h`)

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "signal": "buy",
  "strength": "medium",
  "confidence": 72,
  "current_price": "122379.98",
  "reasons": ["EMA cross up", "RSI oversold"],
  "rules": [
    {"name": "EMA Cross", "passed": true, "score": 30, "reason": "..."}
  ],
  "buy_score": 65,
  "sell_score": 15,
  "stop_loss": "118000",
  "take_profit": "128000",
  "risk_reward": "1.5",
  "indicators": {"rsi_14": "35.2", "ema_9": "..."}
}
```

### `GET /v1/signals/{symbol}/multi`

سیگنال چند‌تایم‌فریمی (confluence).

### `GET /v1/signals/indicators/{symbol}`

محاسبه‌ی همه‌ی اندیکاتورها.

### `GET /v1/signals/levels/{symbol}`

سطوح حمایت و مقاومت (Pivot + Swing).

---

## Scanner

اسکنر بازار با pagination.

### `GET /v1/scanner/list`

لیست نمادها با pagination.

**Query Params:** `page`, `page_size`, `quote`

### `GET /v1/scanner/scan`

اسکن همه یا بخشی از بازار و رتبه‌بندی بر اساس trend.

**Response:**
```json
{
  "count": 20,
  "items": [
    {
      "symbol": "SOLUSDT",
      "current_price": "150.25",
      "trend_score": 85,
      "direction": "bullish",
      "strength": "strong",
      "pattern": "trending",
      "signal": "buy",
      "sparkline": [100.5, 105.2, 110.1, ...]
    }
  ]
}
```

---

## Bots

مدیریت ربات‌های معاملاتی.

### `GET /v1/bots`

لیست همه‌ی ربات‌های ثبت‌شده.

**Response:**
```json
{
  "count": 5,
  "bots": [
    {
      "slug": "trend_follow",
      "name": "روندر",
      "name_en": "Trend Follow Bot",
      "version": "0.1.0",
      "description": "دنبال کردن روند صعودی با EMA Cross و ADX",
      "tags": ["trend_following", "momentum"],
      "capabilities": ["paper", "live", "backtest"],
      "author": "ROSHD_SARV"
    }
  ]
}
```

### `GET /v1/bots/{slug}`

اطلاعات یک ربات.

### `GET /v1/bots/{slug}/status`

وضعیت کامل ربات (positions, trades, equity curve).

### `POST /v1/bots/{slug}/start`

شروع ربات.

### `POST /v1/bots/{slug}/stop`

توقف ربات.

### `POST /v1/bots/{slug}/reset`

ریست state ربات.

---

## Bot Management

مدیریت بودجه.

### `GET /v1/bot/budget`

دریافت وضعیت بودجه.

**Response:**
```json
{
  "allocated_budget": "300000",
  "in_use_capital": "0",
  "available_for_trade": "300000",
  "currency": "TMN"
}
```

### `POST /v1/bot/budget`

آپدیت بودجه.

**Body:**
```json
{
  "allocated_budget": 500000
}
```

---

## Profitability

محاسبه‌ی سود و زیان قبل از معامله.

### `POST /v1/profitability/evaluate`

محاسبه‌ی سود با snapshot فعلی orderbook.

**Body:**
```json
{
  "symbol": "XRPTMN",
  "order_type": "maker",
  "capital": 1000000,
  "slippage_pct": 0.1
}
```

**Response:**
```json
{
  "symbol": "XRPTMN",
  "order_type": "maker",
  "best_bid": "289000",
  "best_ask": "289500",
  "spread": "500",
  "spread_pct": "0.17",
  "capital": "1000000",
  "applied_fee_rate": "0.2",
  "effective_buy_price": "289500",
  "effective_sell_price": "289000",
  "gross_profit": "1727.11",
  "buy_fee": "2000",
  "sell_fee": "2000",
  "total_cost": "4000",
  "net_profit": "-2272.89",
  "net_profit_pct": "-0.23",
  "min_profitable_spread": "0.4",
  "is_profitable": false,
  "notes": ["فاصله bid/ask کمتر از حد سوددهی"]
}
```

### `POST /v1/profitability/evaluate-with-snapshot`

همون، ولی با best_bid/best_ask به‌عنوان query params.

---

## Simulation

شبیه‌ساز ربات‌ها روی داده‌ی تاریخی.

### `GET /v1/simulation/available-dates`

لیست تاریخ‌های قابل انتخاب.

**Query Params:** `days` (پیش‌فرض: 90)

**Response:**
```json
{
  "dates": [
    {
      "gregorian": "2026-10-02",
      "jalali": "1405/07/10",
      "jalali_pretty": "10 مهر 1405"
    }
  ]
}
```

### `GET /v1/simulation/bots`

لیست ربات‌های قابل شبیه‌سازی.

**Response:**
```json
{
  "count": 3,
  "bots": [
    {
      "slug": "trend_follow",
      "name": "روندر",
      "experimental": false
    },
    {
      "slug": "mean_revert",
      "name": "کف‌زن",
      "experimental": true,
      "warning": "این ربات برای تایم‌فریم 15m طراحی شده..."
    }
  ]
}
```

### `GET /v1/simulation/symbols`

لیست نمادهای قابل شبیه‌سازی (۸ نماد).

### `POST /v1/simulation/run`

اجرای شبیه‌سازی یک ربات.

**Query Params:**

| پارامتر | نوع | الزام | توضیح |
|---------|-----|-------|-------|
| `start_date` | string | ✅ | YYYY-MM-DD یا شمسی |
| `end_date` | string | ✅ | YYYY-MM-DD یا شمسی |
| `symbol` | string | ❌ | پیش‌فرض: BTCUSDT |
| `bot_slug` | string | ❌ | اگه خالی، استراتژی پیش‌فرض |
| `initial_balance` | float | ❌ | پیش‌فرض: 1000 |

**مثال:**
```bash
curl -X POST "http://127.0.0.1:8000/v1/simulation/run?start_date=2026-09-02&end_date=2026-10-02&symbol=ETHUSDT&bot_slug=volatility_hunter&initial_balance=1000"
```

**Response:**
```json
{
  "status": "success",
  "symbol": "ETHUSDT",
  "bot_slug": "volatility_hunter",
  "timeframe": "1h",
  "fee_pct": 0.2,
  "position_size_pct": 30.0,
  "prices_count": 695,
  "trades": [
    {"i": 132, "side": "BUY", "price": 3421.5, "reason": "نزدیک کف range"},
    {"i": 141, "side": "SELL", "price": 3580.2, "reason": "take_profit", "pnl": 15.8}
  ],
  "pnl_report": {
    "initial_balance": 1000.0,
    "final_balance": 1039.4,
    "total_pnl": 39.4,
    "pnl_pct": 3.94,
    "total_trades": 5,
    "wins": 4,
    "losses": 1,
    "win_rate": 80.0
  },
  "dates": {
    "start": {"gregorian": "2026-09-02", "jalali": "1405/06/11"},
    "end": {"gregorian": "2026-10-02", "jalali": "1405/07/10"}
  }
}
```

### `POST /v1/simulation/compare`

مقایسه‌ی همه‌ی ربات‌ها روی یک نماد و بازه.

**Query Params:** مثل `run` + `initial_balance`

**Response:**
```json
{
  "symbol": "ETHUSDT",
  "dates": {...},
  "results": [
    {
      "bot_slug": "volatility_hunter",
      "bot_name": "نوسان‌گیر",
      "total_trades": 5,
      "win_rate": 80.0,
      "pnl_pct": 3.94,
      "final_balance": 1039.4,
      "status": "success"
    },
    {
      "bot_slug": "mean_revert",
      "pnl_pct": -0.74,
      "experimental": true
    }
  ]
}
```

**نکته:** نتایج نزولی بر اساس `pnl_pct` مرتب می‌شن.

---

## Paper Trading v1

Paper Trading نسخه‌ی اول (قدیمی).

### `GET /v1/paper/status`

وضعیت Paper Trading.

### `POST /v1/paper/start`

شروع.

### `POST /v1/paper/stop`

توقف.

### `POST /v1/paper/reset`

ریست.

### `POST /v1/paper/run-once`

اجرای یک چرخه (برای تست).

---

## Paper Trading v2

نسخه‌ی دوم با dispatcher هوشمند.

### `GET /v1/paper-v2/status`

**Response:**
```json
{
  "is_running": true,
  "initial_capital": 300000.0,
  "capital": 300000.0,
  "total_return_pct": 0.0,
  "total_trades": 0,
  "wins": 0,
  "losses": 0,
  "win_rate": 0,
  "open_positions": [],
  "recent_trades": [],
  "equity_curve": [],
  "active_symbols": ["BTCTMN", "ETHTMN"]
}
```

### `POST /v1/paper-v2/start`

شروع Paper Trading v2 (نیاز به exchange).

### `POST /v1/paper-v2/stop`

توقف.

### `POST /v1/paper-v2/reset`

ریست state.

---

## Historical Replay

پخش مجدد کندل‌های تاریخی به‌صورت زمان‌بندی‌شده.

### `GET /v1/replay/status`

وضعیت replay.

**Response:**
```json
{
  "is_running": true,
  "mode": "replay",
  "start_date": "2026-09-01",
  "end_date": "2026-09-03",
  "progress_pct": 19.9,
  "processed_candles": 4300,
  "total_candles": 21605,
  "capital": 291795.3,
  "total_trades": 31,
  "wins": 10,
  "losses": 21
}
```

### `POST /v1/replay/start`

شروع replay با پارامترهای بازه و speed.

### `POST /v1/replay/stop`

توقف.

### `POST /v1/replay/reset`

ریست.

---

## Backtest

بک‌تست ساده.

### `GET /v1/backtest/run/{symbol}`

اجرای بک‌تست روی یک نماد.

**Query Params:** `start_date`, `end_date`, `strategy`

---

## Scalping

بک‌تست استراتژی اسکالپینگ.

### `GET /v1/scalping/backtest`

**Query Params:** `symbol`, `start_date`, `end_date`

---

## ML Bottom

مدل ML برای کف‌شناسی.

### `GET /v1/ml/bottom/predict/{symbol}`

پیش‌بینی احتمال کف بودن.

**Response:**
```json
{
  "symbol": "BTCTMN",
  "is_bottom": true,
  "probability": 0.78,
  "features": {...}
}
```

---

## لینک‌های مرتبط

- [ARCHITECTURE.md](./ARCHITECTURE.md) — معماری پروژه
- [SETUP.md](./SETUP.md) — راه‌اندازی
- [BOTS.md](./BOTS.md) — راهنمای ربات‌ها
- [ML_JOURNEY.md](./ML_JOURNEY.md) — سفر ML

---

**پایان مستند — نسخه ۱.۰**
