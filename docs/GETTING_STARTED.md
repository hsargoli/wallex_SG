# 🚀 شروع کار — پلتفرم والکس

> راهنمای کامل برای AI یا توسعه‌دهنده‌ای که می‌خواهد این پروژه را بشناسد و روی آن کار کند.

**آخرین به‌روزرسانی:** 2026-10-06
**نسخه:** 1.0

---

## 📖 فهرست

1. [این پروژه چیه؟](#این-پروژه-چیه)
2. [وضعیت فعلی](#وضعیت-فعلی)
3. [ساختار پوشه‌ها](#ساختار-پوشهها)
4. [راه‌اندازی سریع](#راهاندازی-سریع)
5. [قواعد کار](#قواعد-کار)
6. [معماری کلان](#معماری-کلان)
7. [کارهای در جریان](#کارهای-در-جریان)
8. [مستندات اصلی](#مستندات-اصلی)
9. [لاگ کامیت‌های اخیر](#لاگ-کامیتهای-اخیر)

---

## این پروژه چیه؟

**Wallex Trading Platform** — یک پلتفرم معاملات الگوریتمی روی صرافی والکس (wallex.ir).

### قابلیت‌ها
- ۶ ربات معاملاتی با استراتژی مستقل
- شبیه‌ساز بک‌تست روی داده واقعی والکس
- Paper Trading (شبیه‌سازی زنده)
- Live Order (LIMIT + STOP_LIMIT روی API واقعی والکس)
- مدیریت بودجه per-bot
- ۴۷ endpoint REST

### تکنولوژی
- **Backend:** FastAPI + Python 3.12 + DDD
- **Frontend:** Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui
- **Database:** فعلاً in-memory (Postgres در برنامه)

---

## وضعیت فعلی

| بخش | وضعیت |
|---|---|
| Backend (DDD) | ✅ کامل |
| Frontend (۱۵ صفحه) | ✅ کامل |
| تست‌ها | ✅ ۷۶ پاس |
| Shبیه‌ساز | ✅ کار می‌کند |
| Live Order | ✅ تست‌شده روی والکس |
| Live Loop | 🚧 در حال |
| Postgres | 🔜 در برنامه |

---

## ساختار پوشه‌ها

```
~/wallex/
├── backend/                    ← FastAPI + Python 3.12
│   ├── app/
│   │   ├── domain/             ← Entities، Ports، Value Objects
│   │   ├── application/        ← Use Cases
│   │   ├── infrastructure/     ← Wallex adapter، mapper
│   │   ├── presentation/       ← API routers (۴۷ endpoint)
│   │   └── services/           ← منطق کسب‌وکار + ۶ ربات
│   ├── tests/                  ← ۷۶ تست
│   └── pyproject.toml
│
├── frontend/                   ← Next.js 16 + TS
│   ├── app/                    ← ۱۵ صفحه
│   ├── components/             ← UI، charts، dashboard، bots
│   └── lib/                    ← api، queries، format، hooks
│
└── docs/                       ← مستندات
    ├── GETTING_STARTED.md      ← همین فایل
    ├── ARCHITECTURE.md         ← معماری کلان
    ├── SETUP.md                ← راه‌اندازی تفصیلی
    ├── API.md                  ← مستندات endpointها
    ├── BOTS.md                 ← فهرست ربات‌ها
    ├── bots/                   ← مستند هر ربات
    └── reports/                ← گزارش‌های روزانه
```

---

## راه‌اندازی سریع

### پیش‌نیاز
- Python 3.12+
- uv
- Node.js 20+

### Backend
```
cd ~/wallex/backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```
cd ~/wallex/frontend
npm install
npm run dev
```

### دسترسی
- Backend: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Frontend: http://localhost:3000

### راه‌اندازی تفصیلی
[SETUP.md](./SETUP.md)

---

## قواعد کار

### ⚠️ سه قاعده طلایی

**۱. همیشه قبل و بعد از تغییر، شاهد بگیر**
```
wc -l file                    # تعداد خطوط
head -1 file                  # خط اول
tail -1 file                  # خط آخر
git status --short            # وضعیت git
```

**۲. برای تغییرات حساس، Python (نه sed)**
```
python3 << 'PYEOF'
from pathlib import Path
p = Path("file.md")
src = p.read_text(encoding="utf-8")
old = "متن قدیمی"
new = "متن جدید"
if old not in src:
    raise SystemExit("❌ متن پیدا نشد")
if src.count(old) != 1:
    raise SystemExit(f"❌ انتظار ۱، پیدا شد {src.count(old)}")
p.write_text(src.replace(old, new, 1), encoding="utf-8")
print("✅ تغییر اعمال شد")
PYEOF
```

**۳. markdown با سه‌مرحله**
- AI محتوا با ` (backtick) و ``` (code block) می‌فرستد
- کاربر در LANG=C nano پیست می‌کند
- AI با Python تبدیل می‌کند

### قواعد کامل
در `docs/06-development/CONVENTIONS.md` (بعداً منتقل می‌شود)

---

## معماری کلان

### لایه‌ها (DDD)
```
Presentation (FastAPI)
       ↓
Application (Use Cases)
       ↓
Domain (Entities) ← Infrastructure (Wallex)
       ↑
Services (Robots, Simulator)
```

### قاعده
جهت وابستگی همیشه به سمت Domain.

**مستندات کامل:** [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## کارهای در جریان

### 🚧 الان
- چارت کامل (EMA + RSI + MACD)
- Live Engine برای ربات‌ها
- صفحه `/bots` بهتر

### 🔜 بعد
- Postgres برای persistence
- ربات‌های جدید (Bollinger، MACD، DCA)
- WebSocket برای قیمت زنده

---

## مستندات اصلی

| فایل | محتوا |
|---|---|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | معماری + لایه‌ها |
| [SETUP.md](./SETUP.md) | راه‌اندازی گام‌به‌گام |
| [API.md](./API.md) | ۴۷ endpoint |
| [BOTS.md](./BOTS.md) | فهرست ربات‌ها |
| [bots/](./bots/) | مستند هر ربات |
| [reports/](./reports/) | گزارش‌های توسعه |

---

## لاگ کامیت‌های اخیر

```
(بعداً با git log پر می‌شود)
```

---

**پایان مستند — نسخه ۱.۰**

