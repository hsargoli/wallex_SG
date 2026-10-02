# 🐍 Backend — Wallex Trading Platform

> Backend پلتفرم معاملات الگوریتمی والکس — FastAPI + Python 3.12 + DDD

**نسخه:** 0.1.0
**تیم:** ROSHD_SARV

---

## 📖 فهرست

1. [نگاه کلی](#نگاه-کلی)
2. [تکنولوژی‌ها](#تکنولوژیها)
3. [ساختار پروژه](#ساختار-پروژه)
4. [نصب و راه‌اندازی](#نصب-و-راهاندازی)
5. [اجرا](#اجرا)
6. [معماری](#معماری)
7. [تست‌ها](#تستها)
8. [ابزارها](#ابزارها)
9. [لینک‌های مرتبط](#لینکهای-مرتبط)

---

## نگاه کلی

Backend این پروژه یک **API مبتنی بر FastAPI** است که با معماری **DDD (Domain-Driven Design)** طراحی شده.

### ویژگی‌ها

- **۴۴ endpoint** در ۱۵ گروه
- **۵ ربات معاملاتی** با Adapter Pattern
- **DDD + Hexagonal Architecture**
- **Decimal** برای دقت مالی
- **structlog** برای لاگ JSON
- **RFC-7807** error handling
- **۷۶ تست** با pytest

### آمار

| متریک | مقدار |
|-------|-------|
| فایل‌های Python | ۱۰۵ |
| Endpointها | ۴۴ |
| تست‌ها | ۷۶ (۱۰۰٪ پاس) |
| Ruff | ✅ 0 errors |
| Python | 3.12+ |

---

## تکنولوژی‌ها

| کتابخانه | نسخه | کاربرد |
|----------|------|--------|
| **FastAPI** | 0.115+ | وب فریمورک |
| **Pydantic** | 2.x | اعتبارسنجی |
| **httpx** | 0.27+ | HTTP client (async) |
| **structlog** | 24.x | لاگ ساخت‌یافته |
| **pydantic-settings** | 2.x | تنظیمات از env |
| **jdatetime** | 5.x | تاریخ شمسی |
| **pytest** | 9.x | تست |
| **ruff** | 0.16+ | linting |

مدیریت پکیج: **uv** (به جای pip/poetry)

---

## ساختار پروژه

```
backend/
├── app/
│   ├── main.py               ← Application Factory
│   ├── core/                 ← config, logging, exceptions
│   ├── domain/               ← ❤️ قلب سیستم (بدون وابستگی)
│   │   ├── entities/         ← Candle, Market, Balance
│   │   ├── models/           ← Budget, Profitability
│   │   ├── ports/            ← ExchangePort
│   │   └── value_objects/    ← Symbol
│   ├── application/
│   │   └── use_cases/        ← ۶ use case
│   ├── infrastructure/
│   │   ├── exchange/wallex/  ← client, mapper
│   │   └── wallex_repo.py    ← MarketDataRepository
│   ├── presentation/
│   │   └── api/
│   │       ├── deps.py
│   │       └── v1/           ← ۱۴ router
│   │           └── router.py ← master router
│   └── services/             ← ۴۹ فایل منطق
│       ├── indicators.py
│       ├── bot_simulator.py
│       ├── bots/             ← ۵ ربات
│       └── ...
├── scripts/
│   ├── tools/                ← ابزارهای روزمره
│   ├── ml/                   ← ML فعال
│   └── archive/              ← آرشیو کامل
├── tests/
│   ├── unit/
│   └── integration/
├── data/                     ← runtime (models, state)
├── pyproject.toml
└── README.md                 ← همین فایل
```

📚 **ساختار کامل:** [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

---

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.12+
- uv ([نصب](https://docs.astral.sh/uv/))

### نصب

```bash
cd ~/wallex/backend
uv sync
```

### تنظیمات

فایل `.env` در ریشه پروژه (`~/wallex/.env`) باید `WALLEX_API_KEY` رو داشته باشه:

```env
WALLEX_API_KEY="your-key-here"
WALLEX_BASE_URL="https://api.wallex.ir"
```

---

## اجرا

### حالت توسعه

```bash
cd ~/wallex/backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### دسترسی‌ها

| سرویس | URL |
|-------|-----|
| **API** | http://127.0.0.1:8000 |
| **Swagger UI** | http://127.0.0.1:8000/docs |
| **ReDoc** | http://127.0.0.1:8000/redoc |
| **OpenAPI JSON** | http://127.0.0.1:8000/openapi.json |

---

## معماری

### لایه‌ها

```
Presentation (FastAPI)  →  Application (Use Cases)
                              ↓
                       Domain (Entities)  ←  Infrastructure (Wallex)
```

**قاعده:** جهت وابستگی همیشه به سمت Domain است.

### Routers

۱۴ router که توسط master router مدیریت می‌شن:

```
/v1/markets       /v1/account       /v1/bot
/v1/bots          /v1/profitability /v1/signals
/v1/scanner       /v1/backtest      /v1/scalping
/v1/ml/bottom     /v1/paper         /v1/paper-v2
/v1/replay        /v1/simulation
```

📚 **جزئیات:** [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

---

## تست‌ها

```bash
cd ~/wallex/backend

# همه تست‌ها
uv run pytest tests/ -v

# فقط unit
uv run pytest tests/unit/ -v

# فقط integration
uv run pytest tests/integration/ -v

# با coverage
uv run pytest --cov=app --cov-report=html
```

**نتیجه:** 76 passed ✅

---

## ابزارها

### Linting با ruff

```bash
# چک
uv run ruff check app/

# fix خودکار
uv run ruff check app/ --fix
```

### Type checking

پروژه از **type hints** کامل استفاده می‌کنه. برای چک:

```bash
uv run python -c "from app.main import app; print('OK')"
```

### Development tools

| ابزار | دستور |
|-------|-------|
| `ruff` | `uv run ruff check app/` |
| `pytest` | `uv run pytest tests/` |
| `coverage` | `uv run pytest --cov=app` |

---

## ورودی‌های API والکس

**نکات مهم:**

| مورد | محدودیت |
|------|---------|
| تایم‌فریم `1h` | فقط ~۷۲۰ کندل آخر (≈۳۰ روز) |
| تایم‌فریم `1D` | نامحدود |
| `15m`, `5m`, `30m`, `4h` | پشتیبانی نمی‌شن |

**API Key:**
- فقط `Read` دسترسی
- **هرگز** `Withdraw` رو فعال نکن
- اگه کلید لو رفت → فوراً revoke

---

## لینک‌های مرتبط

### مستندات اصلی

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) — معماری کامل
- [SETUP.md](../docs/SETUP.md) — راه‌اندازی گام‌به‌گام
- [API.md](../docs/API.md) — مستندات endpointها
- [BOTS.md](../docs/BOTS.md) — راهنمای ربات‌ها

### گزارش‌ها

- [docs/reports/](../docs/reports/) — گزارش‌های روزانه

### منابع خارجی

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [uv Docs](https://docs.astral.sh/uv/)
- [Wallex API](https://wallex.ir)

---

**پایان — نسخه ۰.۱.۰**
