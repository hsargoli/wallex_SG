# 🚀 Setup Guide — Wallex Trading Platform

> راهنمای کامل راه‌اندازی محیط توسعه، اجرا، و تست پروژه.

**آخرین به‌روزرسانی:** ۲۰۲۶-۱۰-۰۲
**نسخه:** 1.0
**زمان تخمینی راه‌اندازی:** ۲۰-۳۰ دقیقه

---

## 📖 فهرست

1. [پیش‌نیازها](#پیشنیازها)
2. [کلون کردن پروژه](#کلون-کردن-پروژه)
3. [تنظیمات محیطی](#تنظیمات-محیطی)
4. [راه‌اندازی Backend](#راهاندازی-backend)
5. [راه‌اندازی Frontend](#راهاندازی-frontend)
6. [اجرای پروژه](#اجرای-پروژه)
7. [اجرای تست‌ها](#اجرای-تستها)
8. [ابزارهای توسعه](#ابزارهای-توسعه)
9. [مشکلات رایج](#مشکلات-رایج)
10. [گردش کار توسعه](#گردش-کار-توسعه)

---

## پیش‌نیازها

### سیستم‌عامل

- **Linux** (توصیه‌شده — Ubuntu 22.04+ یا معادل)
- **macOS** (نسخه 12+)
- **Windows** (با WSL2)

### نرم‌افزارهای لازم

| ابزار | نسخه | کاربرد |
|-------|------|--------|
| **Python** | 3.12+ | Backend |
| **uv** | 0.4+ | مدیریت پکیج Python |
| **Node.js** | 20+ | Frontend |
| **npm** | 10+ | مدیریت پکیج Node |
| **Git** | 2.30+ | نسخه‌بندی |

### نصب پیش‌نیازها (Ubuntu/Debian)

```bash
# Python
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip

# uv (مدیریت پکیج Python)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 20 (از طریق NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Git
sudo apt install -y git
```

### تأیید نصب

```bash
python3.12 --version   # باید 3.12.x چاپ کنه
uv --version           # باید 0.4.x یا بالاتر
node --version         # باید v20.x یا بالاتر
npm --version          # باید 10.x یا بالاتر
git --version          # باید 2.30.x یا بالاتر
```

---

## کلون کردن پروژه

```bash
# کلون
git clone <repo-url> ~/wallex
cd ~/wallex

# چک ساختار
ls -la
# باید ببینی: backend/ frontend/ docs/ README.md .env.example
```

---

## تنظیمات محیطی

### ۱. کپی `.env.example` به `.env`

```bash
cd ~/wallex
cp .env.example .env
```

### ۲. ویرایش `.env`

```bash
nano .env
```

**محتویات لازم:**

```env
# --- App ---
PROJECT_NAME="Wallex Platform"
ENV="development"
DEBUG=True
LOG_LEVEL="INFO"

# --- Wallex Exchange ---
WALLEX_BASE_URL="https://api.wallex.ir"
WALLEX_WS_URL="wss://api.wallex.ir/ws"
WALLEX_API_KEY="your-api-key-here"
WALLEX_TIMEOUT_SECONDS=10
WALLEX_MAX_CONNECTIONS=20

# --- Cache ---
CACHE_TTL_SECONDS=5
```

### ۳. دریافت API Key از والکس

1. برو به [wallex.ir](https://wallex.ir)
2. ثبت‌نام / ورود
3. پنل کاربری → **API Keys**
4. **Create New Key** → دسترسی‌های لازم:
   - ✅ Read (خواندن)
   - ❌ Withdraw (برداشت) — **هرگز فعال نکن!**
   - ❌ Trade (معامله) — فعلاً لازم نیست
5. کلید رو کپی کن و در `.env` بذار

### ⚠️ نکات امنیتی مهم

- **هرگز** API Key رو کامیت نکن
- **هرگز** Withdraw رو فعال نکن
- اگه کلید لو رفت → **فوراً revoke کن**
- دسترسی فایل `.env` باید `600` باشه:

```bash
chmod 600 .env
```

---

## راه‌اندازی Backend

### ۱. نصب وابستگی‌ها

```bash
cd ~/wallex/backend
uv sync
```

این دستور:
- یه محیط مجازی (`.venv`) می‌سازه
- وابستگی‌ها رو نصب می‌کنه
- `uv.lock` رو می‌خونه

### ۲. تأیید نصب

```bash
uv run python -c "from app.main import app; print('✅ OK')"
```

باید چاپ کنه: `✅ OK`

### ۳. اجرای سریع (تست import)

```bash
cd ~/wallex/backend
uv run python -c "
from app.main import app
print(f'مسیرها: {len(app.openapi()[\"paths\"])}')
"
```

باید ببینی: `مسیرها: 44`

---

## راه‌اندازی Frontend

### ۱. نصب وابستگی‌ها

```bash
cd ~/wallex/frontend
npm install
```

### ۲. تأیید نصب

```bash
npm run build
```

اگه خطا نداد → آماده‌ست.

---

## اجرای پروژه

### ترمینال ۱ — Backend

```bash
cd ~/wallex/backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

باید ببینی:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### ترمینال ۲ — Frontend

```bash
cd ~/wallex/frontend
npm run dev
```

باید ببینی:

```
▲ Next.js 16.3.7
- Local:        http://localhost:3000
✓ Ready in 2.5s
```

### دسترسی‌ها

| سرویس | URL |
|-------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

---

## اجرای تست‌ها

### Backend — pytest

```bash
cd ~/wallex/backend

# همه تست‌ها
uv run pytest tests/ -v

# فقط unit
uv run pytest tests/unit/ -v

# فقط integration
uv run pytest tests/integration/ -v

# با coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Frontend — TypeScript check

```bash
cd ~/wallex/frontend
npx tsc --noEmit
```

### Frontend — ESLint

```bash
cd ~/wallex/frontend

# چک
npm run lint

# fix خودکار
npm run lint:fix
```

---

## ابزارهای توسعه

### Backend

| ابزار | دستور | کاربرد |
|-------|-------|--------|
| **ruff** | `uv run ruff check app/` | linting |
| **ruff fix** | `uv run ruff check app/ --fix` | fix خودکار |
| **pytest** | `uv run pytest tests/` | تست |
| **coverage** | `uv run pytest --cov=app` | پوشش تست |

### Frontend

| ابزار | دستور | کاربرد |
|-------|-------|--------|
| **TypeScript** | `npx tsc --noEmit` | type check |
| **ESLint** | `npm run lint` | linting |
| **Next.js build** | `npm run build` | build production |

---

## مشکلات رایج

### ۱. خطای `ModuleNotFoundError: No module named 'app'`

**علت:** اجرای پایتون از مسیر اشتباه

**راه‌حل:** همیشه از پوشه `backend/` اجرا کن:

```bash
cd ~/wallex/backend
uv run python ...
```

### ۲. خطای `WALLEX_API_KEY is required`

**علت:** فایل `.env` ناقصه یا API Key خالیه

**راه‌حل:**

```bash
cd ~/wallex
cat .env | grep WALLEX_API_KEY
```

اگه خالی بود، یه API Key جدید از پنل والکس بگیر.

### ۳. خطای `Connection refused` برای Backend

**علت:** Backend اجرا نشده یا پورت 8000 اشغاله

**راه‌حل:**

```bash
# چک کن چه پروسه‌ای پورت 8000 رو گرفته
sudo lsof -i :8000

# اگه چیز اضافیه، بکشش
kill -9 <PID>
```

### ۴. خطای `port 3000 already in use`

**علت:** یه Next.js دیگه در حال اجراست

**راه‌حل:**

```bash
# کشتن پروسه‌های Next.js
pkill -f "next dev"

# یا اجرا روی پورت دیگه
npm run dev -- -p 3001
```

### ۵. خطای API والکس — `no_data`

**علت:** درخواست برای بازه‌ی تاریخی که داده‌ش موجود نیست

**محدودیت‌های API والکس:**

| تایم‌فریم | محدودیت |
|-----------|---------|
| `1h` | فقط ~۳۰ روز آخر |
| `1D` | نامحدود |
| `15m`, `5m`, `1h`, `4h` | پشتیبانی نمی‌شن |

**راه‌حل:** از تایم‌فریم `1h` یا `1D` استفاده کن.

### ۶. خطای `coroutine was never awaited`

**علت:** فراخوانی async بدون await

**راه‌حل:** مطمئن شو همه‌ی توابع async با `await` صدا زده می‌شن.

---

## گردش کار توسعه

### ۱. شروع روز کاری

```bash
# آخرین تغییرات
cd ~/wallex
git pull

# نصب وابستگی‌های جدید (اگه هست)
cd backend && uv sync
cd ../frontend && npm install
```

### ۲. کدنویسی

- **Backend:** الگوی DDD رو دنبال کن
- **Frontend:** از hooks های موجود استفاده کن
- **تست:** برای هر feature جدید، تست بنویس

### ۳. قبل از کامیت

```bash
# Backend
cd ~/wallex/backend
uv run ruff check app/
uv run pytest tests/

# Frontend
cd ~/wallex/frontend
npx tsc --noEmit
npm run lint
```

### ۴. کامیت

```bash
cd ~/wallex
git add -A
git status   # حتماً چک کن

git commit -m "type(scope): توضیح کوتاه"
```

**Conventional Commits:**

| Type | کاربرد |
|------|--------|
| `feat` | قابلیت جدید |
| `fix` | رفع باگ |
| `refactor` | بازنویسی کد |
| `docs` | مستندات |
| `test` | تست |
| `chore` | کارهای جانبی |

---

## ساختار پروژه — یادآور

```
wallex/
├── backend/         ← FastAPI + Python
├── frontend/        ← Next.js + TypeScript
├── docs/            ← مستندات
│   ├── ARCHITECTURE.md
│   ├── SETUP.md     ← همین فایل
│   ├── API.md
│   └── BOTS.md
└── README.md
```

---

## لینک‌های مرتبط

- [ARCHITECTURE.md](./ARCHITECTURE.md) — معماری پروژه
- [API.md](./API.md) — مستندات API
- [BOTS.md](./BOTS.md) — راهنمای ربات‌ها
- [ML_JOURNEY.md](./ML_JOURNEY.md) — سفر ML
- [reports/](./reports/) — گزارش‌های روزانه

---

## منابع خارجی

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [uv Docs](https://docs.astral.sh/uv/)
- [Wallex API](https://wallex.ir/api)

---

**پایان مستند — نسخه ۱.۰**
