# 🚀 Wallex Trading Platform

> پلتفرم جامع معاملات الگوریتمی، شبیه‌سازی و Paper Trading روی صرافی والکس

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org)
[![Tests](https://img.shields.io/badge/tests-76%20passing-brightgreen)](#اجرای-تستها)

---

## 📖 فهرست

1. [معرفی](#معرفی)
2. [ویژگی‌ها](#ویژگیها)
3. [تکنولوژی‌ها](#تکنولوژیها)
4. [نصب سریع](#نصب-سریع)
5. [اجرا](#اجرا)
6. [ساختار پروژه](#ساختار-پروژه)
7. [مستندات](#مستندات)
8. [وضعیت پروژه](#وضعیت-پروژه)
9. [اجرای تست‌ها](#اجرای-تستها)
10. [مشارکت](#مشارکت)

---

## معرفی

**Wallex Trading Platform** یک سیستم کامل برای:

- **📊 تحلیل بازار** — قیمت لحظه‌ای، کندل‌ها، orderbook، اندیکاتورها
- **🤖 ۵ ربات معاملاتی** — روندر، نوسان‌گیر، کف‌زن، Grid، Smart Portfolio
- **🔄 شبیه‌سازی تاریخی** — بک‌تست ربات‌ها روی داده‌ی واقعی والکس
- **📈 Paper Trading** — تست زنده‌ی استراتژی بدون پول واقعی
- **💰 مدیریت ریسک** — بودجه، sizing، SL/TP
- **🎯 محاسبه سود** — ارزیابی profitability قبل از معامله
- **🔔 سیگنال‌ها** — خرید/فروش با تحلیل چند‌تایم‌فریمی

### برای کی؟

- **تریدرها** — برای بک‌تست استراتژی‌های خود
- **توسعه‌دهنده‌ها** — برای ساخت ربات‌های جدید
- **تحلیلگران** — برای مطالعه‌ی رفتار بازار

---

## ویژگی‌ها

### Backend (FastAPI + Python)

- ✅ معماری **DDD** (Domain-Driven Design) + Hexagonal
- ✅ **۴۴ endpoint** در ۱۵ گروه
- ✅ **۵ ربات** با معماری Adapter
- ✅ **شبیه‌ساز** با رفع look-ahead bias
- ✅ **RFC-7807** error handling
- ✅ **structured logging** (structlog)
- ✅ **Decimal** برای دقت مالی
- ✅ **۷۶ تست** (۱۰۰٪ پاس)

### Frontend (Next.js + TypeScript)

- ✅ **صفحات کامل فارسی** (RTL + Vazirmatn)
- ✅ **۱۰ صفحه** کاربردی
- ✅ **تاریخ شمسی** کامل
- ✅ **نمودار کندل** با lightweight-charts
- ✅ **shadcn/ui** برای UI
- ✅ **React Query** برای state
- ✅ **TypeScript strict** (0 errors)
- ✅ **ESLint 9** (0 warnings)

---

## تکنولوژی‌ها

### Backend

| تکنولوژی | نسخه | کاربرد |
|-----------|------|--------|
| Python | 3.12+ | زبان اصلی |
| FastAPI | 0.115+ | وب فریمورک |
| Pydantic | 2.x | اعتبارسنجی |
| httpx | 0.27+ | HTTP client |
| structlog | 24.x | لاگ ساخت‌یافته |
| pytest | 9.x | تست |
| ruff | 0.16+ | linting |
| uv | 0.4+ | مدیریت پکیج |

### Frontend

| تکنولوژی | نسخه | کاربرد |
|-----------|------|--------|
| Next.js | 16.3+ | React framework |
| TypeScript | 5.x | زبان |
| Tailwind CSS | 4.x | styling |
| shadcn/ui | — | کامپوننت |
| React Query | 5.x | data fetching |
| lucide-react | — | آیکون |
| lightweight-charts | — | نمودار |

---

## نصب سریع

### پیش‌نیازها

- Python 3.12+
- Node.js 20+
- uv ([نصب](https://docs.astral.sh/uv/))
- Git

### ۳ دستور برای راه‌اندازی

```bash
# ۱. کلون
git clone <repo-url> ~/wallex && cd ~/wallex

# ۲. تنظیمات محیطی
cp .env.example .env
# سپس WALLEX_API_KEY را در .env بذارید

# ۳. نصب وابستگی‌ها
cd backend && uv sync
cd ../frontend && npm install
```

📚 راهنمای کامل: [SETUP.md](./docs/SETUP.md)

---

## اجرا

### ترمینال ۱ — Backend

```bash
cd ~/wallex/backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### ترمینال ۲ — Frontend

```bash
cd ~/wallex/frontend
npm run dev
```

### دسترسی‌ها

| سرویس | URL |
|-------|-----|
| 🌐 داشبورد | http://localhost:3000 |
| 🔌 API | http://127.0.0.1:8000 |
| 📖 Swagger | http://127.0.0.1:8000/docs |
| 📕 ReDoc | http://127.0.0.1:8000/redoc |

---

## ساختار پروژه

```
wallex/
├── backend/              ← FastAPI + Python 3.12
│   ├── app/
│   │   ├── domain/       ← Entities, Ports (بدون وابستگی)
│   │   ├── application/  ← Use Cases
│   │   ├── infrastructure/ ← Wallex adapter
│   │   ├── presentation/ ← API routers (44 endpoint)
│   │   └── services/     ← ربات‌ها، اندیکاتورها، شبیه‌ساز
│   ├── scripts/
│   │   ├── tools/        ← ابزارهای روزمره
│   │   ├── ml/           ← ML فعال
│   │   └── archive/      ← آرشیو کامل
│   └── tests/            ← ۷۶ تست
│
├── frontend/             ← Next.js 16 + TypeScript
│   ├── app/              ← ۱۰ صفحه
│   ├── components/       ← UI components
│   └── lib/              ← API client + hooks
│
└── docs/                 ← مستندات
    ├── ARCHITECTURE.md
    ├── SETUP.md
    ├── API.md
    ├── BOTS.md
    ├── ML_JOURNEY.md
    └── reports/          ← گزارش‌های روزانه
```

---

## مستندات

### راهنماهای اصلی

| مستند | توضیح |
|-------|-------|
| [**ARCHITECTURE.md**](./docs/ARCHITECTURE.md) | معماری کامل، لایه‌ها، جریان داده |
| [**SETUP.md**](./docs/SETUP.md) | راهنمای راه‌اندازی گام‌به‌گام |
| [**API.md**](./docs/API.md) | مستندات ۴۴ endpoint |
| [**BOTS.md**](./docs/BOTS.md) | راهنمای ربات‌ها + اضافه کردن ربات جدید |
| [**ML_JOURNEY.md**](./docs/ML_JOURNEY.md) | سفر ML و درس‌ها |

### گزارش‌های توسعه

گزارش‌های روزانه در [docs/reports/](./docs/reports/) قرار دارن:

- ممیزی امنیت، گیت و کد
- سازماندهی مجدد اسکریپت‌ها
- شبیه‌ساز چندرباتی
- رفع باگ API router

---

## وضعیت پروژه

### Milestones

| # | Milestone | وضعیت |
|---|-----------|-------|
| 1-4 | زیرساخت، اتصال به والکس | ✅ |
| 5 | Market Data Layer | ✅ |
| 6 | Profitability Checker | ✅ |
| 7 | Order Execution | 🚧 در راه |
| 8 | Live Trading | 🔜 |

### آمار

| متریک | مقدار |
|-------|-------|
| Endpointهای API | ۴۴ |
| ربات‌های معاملاتی | ۵ |
| صفحات Next.js | ۱۰ |
| تست‌ها | ۷۶ (۱۰۰٪ پاس) |
| Ruff | ✅ All checks passed |
| TypeScript | ✅ 0 errors |
| ESLint | ✅ 0 warnings |

---

## اجرای تست‌ها

### Backend

```bash
cd ~/wallex/backend
uv run pytest tests/ -v          # ۷۶ تست
uv run pytest --cov=app          # با coverage
```

### Frontend

```bash
cd ~/wallex/frontend
npx tsc --noEmit                 # type check
npm run lint                     # ESLint
```

---

## مشارکت

### قبل از کامیت

```bash
# Backend
cd backend
uv run ruff check app/
uv run pytest tests/

# Frontend
cd frontend
npx tsc --noEmit
npm run lint
```

### فرمت کامیت

از [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): توضیح کوتاه
```

**Type ها:**

- `feat` — قابلیت جدید
- `fix` — رفع باگ
- `refactor` — بازنویسی
- `docs` — مستندات
- `test` — تست
- `chore` — جانبی

---

## ⚠️ هشدار مهم

> **این پروژه آموزشی-تحقیقی است.**
> نتایج بک‌تست تضمین آینده نیستن.
> هر معامله‌ی واقعی با ریسک شخصی انجام می‌شود.
> قبل از Live، حتماً Paper Trading کنید.

---

## لایسنس

MIT License — آزاد برای استفاده، تغییر و توزیع.

---

## تماس

**تیم:** ROSHD_SARV
**صرافی هدف:** [Wallex.ir](https://wallex.ir)

---

**🌟 اگر این پروژه براتون مفید بود، ستاره بدید!**

---

## 📜 README قدیمی

> نسخه‌ی قدیمی README (قبل از بازنویسی) در [`docs/README_OLD.md`](./docs/README_OLD.md) حفظ شده است.

---

**🌟 اگر این پروژه براتون مفید بود، ستاره بدید!**
