# 📐 قواعد توسعه والکس

> قواعد کار روی پروژه Wallex
> نسخه ۱.۰ — مهر ۱۴۰۵
> شرکت: SGPR (سرو پایا رشد سبز)

---

## 🎯 چرا این سند؟

این سند **قواعد مشترک تیم** را مکتوب می‌کند:

- چطور کد بنویسیم
- چطور مستندات بسازیم
- چطور commit کنیم
- چطور از git استفاده کنیم
- چطور معماری و تست را حفظ کنیم

**هدف:** همه‌ی اعضای تیم (انسان و AI) یکسان کار کنند.

**مخاطب:** حسین (صاحب پروژه)، دی (معاون اصلی)، نووآ (AI همکار).

---

## 📝 قاعده ۱ — شاهد گرفتن

### قبل از هر تغییر

```
ls -la file.md              # وجود فایل
wc -l file.md               # تعداد خطوط
head -1 file.md             # خط اول
tail -1 file.md             # خط آخر
grep -n "متن" file.md       # موقعیت
```

### بعد از هر تغییر

```
wc -l file.md               # تعداد خطوط
head -1 file.md             # خط اول
tail -1 file.md             # خط آخر
git status --short          # وضعیت git
```

### قاعده طلایی

> **قبل از هر تغییر، شاهد بگیر.**
> **بعد از هر تغییر، شاهد بگیر.**

---

## 📝 قاعده ۲ — Python برای تغییرات حساس

### چه وقت Python؟

- فایل markdown
- تغییرات دقیق (exact match)
- فایل‌های یونیکد (فارسی، emoji)
- هر چیزی که sed ممکن است خراب کند

### الگوی استاندارد

```
from pathlib import Path

p = Path("file.md")
src = p.read_text(encoding="utf-8")

old = "متن قدیمی"
new = "متن جدید"

# چک‌های امنیتی
if old not in src:
    raise SystemExit("❌ متن قدیمی پیدا نشد")
if src.count(old) != 1:
    raise SystemExit(f"❌ انتظار ۱، پیدا شد {src.count(old)}")

src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("✅ تغییر اعمال شد")
```

### چرا این الگو؟

- **if old not in src** → اگر متن نبود، متوقف شو
- **if src.count(old) != 1** → اگر بیش از ۱ جا بود، متوقف شو
- **encoding="utf-8"** → برای فارسی و emoji

---

## 📝 قاعده ۳ — ابزار مناسب برای کار مناسب

| کار | ابزار |
|---|---|
| markdown | nano (LANG=C) + Python |
| کد Python | nano یا geany |
| کد JS/TS | geany یا VS Code |
| YAML/JSON | nano |
| Bash scripts | nano |
| فایل‌های بزرگ | geany |

### ابزارهای ممنوع برای markdown

- heredoc در ترمینال
- paste مستقیم backtick
- geany با RTL فعال

**جزئیات در:** `docs/MARKDOWN_GUIDE.md` (اگر هست)

---

## 📝 قاعده ۴ — commit کردن

### الگوی پیام commit

```
type(scope): subject

- بدنه (اختیاری)
- هر خط یک تغییر
```

### typeهای مجاز

- **feat** — فیچر جدید
- **fix** — رفع باگ
- **docs** — مستندات
- **chore** — کارهای فنی
- **refactor** — بازنویسی کد
- **test** — تست

### scopeهای والکس

- **bots** — ربات‌ها
- **api** — endpointها
- **frontend** — Next.js
- **backend** — FastAPI / core
- **simulator** — شبیه‌ساز
- **ml** — یادگیری ماشین
- **test** — تست‌ها
- **deps** — وابستگی‌ها
- **docs** — مستندات

### مثال‌های واقعی

```
docs(bots): rewrite BOTS.md as summary (563→225 lines)

- Convert to summary format
- Keep bot list and links
- Move details to docs/bots/

fix(grid_bot): rename capital_per_level_pct to cash_per_level_pct
```

### مثال بد

```
fix stuff
```

---

## 📝 قاعده ۵ — git workflow

### قبل از commit

```
git status --short          # چی تغییر کرده
git diff                    # چطور تغییر کرده
```

### مرحله‌بندی

```
git add file.md             # فایل خاص
git add docs/               # پوشه
git add -p file.md          # انتخاب تعاملی تغییرات
# ❌ از git add -A اجتناب کن — ممکن است .env و لاگ را بفرستد
```

### بعد از commit

```
git log --oneline -3        # تاریخچه
git status --short          # پاک است؟
```

---

## 📝 قاعده ۶ — اندازه فایل‌ها

### قاعده

> **هر سند markdown ≤ ۳۰۰ خط.**
> **اگر بیشتر شد، تکه‌تکه کن.**

### چرا؟

- خواندن آسان‌تر
- commit تمیزتر
- git diff واضح‌تر

### چه وقت تکه‌تکه؟

- سند بالای ۲۰۰ خط
- سند چند موضوع دارد
- سند چند مخاطب دارد

### مثال والکس

**قبل:** `BOTS.md` (۵۶۳ خط) — چند موضوع

**بعد:**
- `docs/BOTS.md` (۲۲۵ خط) — فهرست ربات‌ها
- `docs/bots/README.md` — راهنمای پوشه
- `docs/bots/trend_follow.md` — مستند یک ربات

---

## 📝 قاعده ۷ — ساختار مستندات والکس

### ساختار فعلی

```
~/wallex/
├── README.md                 ← معرفی پروژه
└── docs/
    ├── README.md             ← نقشه‌ی مستندات
    ├── GETTING_STARTED.md    ← شروع کار
    ├── ARCHITECTURE.md       ← معماری
    ├── SETUP.md              ← راه‌اندازی
    ├── API.md                ← ۴۷ endpoint
    ├── BOTS.md               ← فهرست ربات‌ها
    ├── ML_JOURNEY.md         ← سفر ML
    ├── CONVENTIONS.md        ← همین سند
    ├── bots/                 ← مستند هر ربات
    │   ├── README.md
    │   └── trend_follow.md
    └── reports/              ← گزارش‌های روزانه
        ├── README.md
        └── YYYY-MM-DD*.md
```

### قاعده

- **هر سند، یک موضوع**
- **هر پوشه، یک README.md**
- **گزارش‌ها با تاریخ:** `YYYY-MM-DD_عنوان.md`
- **مستند هر ربات:** `docs/bots/نام_ربات.md`

---

## 📝 قاعده ۸ — بازبینی

### چرا بازبینی؟

> **هر سند، هر کد، هر commit — باید بازبینی شود.**
> **حتی سند «قواعد» خودش.**

### چه وقت؟

- **قبل از commit** — خودت یک بار بخوان
- **بعد از commit** — دی یا نووآ بخوانند
- **دوره‌ای** — هر چند هفته

### چه چیزی را بازبینی کنیم؟

| # | مورد |
|---|---|
| ۱ | **صحت فنی** — آیا کد/دستور درست کار می‌کند؟ |
| ۲ | **وضوح** — آیا مخاطب می‌فهمد؟ |
| ۳ | **امنیت** — آیا خطری هست؟ |
| ۴ | **سازگاری** — آیا با قواعد دیگر هماهنگ است؟ |
| ۵ | **به‌روز بودن** — آیا هنوز معتبر است؟ |

### نقش Reviewer

- **دی (DeepSeek)** — معاون اصلی، بازبینی فنی و امنیتی
- **نووآ** — AI همکار، بازبینی فنی
- **حسین** — صاحب پروژه، بازبینی محتوایی و تجربی

---

## 📝 قاعده ۹ — معماری والکس

### اصول

- **DDD (Domain-Driven Design)**
- **Hexagonal Architecture (Ports & Adapters)**

### لایه‌ها

```
Presentation (FastAPI)
       ↓
Application (Use Cases)
       ↓
Domain (Entities, Value Objects, Ports)
       ↑
Infrastructure (Wallex adapter, mapper)
       ↑
Services (Robots, Simulator)
```

### قاعده طلایی

> **جهت وابستگی همیشه به سمت Domain.**

- Domain به هیچ‌چیز وابسته نیست
- Application به Domain وابسته است
- Infrastructure به Domain وابسته است (پیاده‌سازی Portها)
- Presentation به Application وابسته است

### Port و Adapter

- **Port** — interface در Domain (مثل `ExchangePort`)
- **Adapter** — پیاده‌سازی در Infrastructure (مثل `WallexAdapter`)

### ممنوع

- ❌ import از Infrastructure در Domain
- ❌ import از Presentation در Application
- ❌ منطق کسب‌وکار در Infrastructure

**مستندات کامل:** `docs/ARCHITECTURE.md`

---

## 📝 قاعده ۱۰ — تست‌ها

### وضعیت فعلی

- **۷۶ تست پاس**
- فریمورک: pytest (احتمالاً)

### قاعده

> **هر تغییر کد، حداقل یک تست.**

### انواع تست

- **Unit** — Domain، Application
- **Integration** — Infrastructure (Wallex mock)
- **API** — endpointها (FastAPI TestClient)

### اجرا

```
cd ~/wallex/backend
uv run pytest
```

### چه وقت تست بنویسیم؟

- فیچر جدید → تست جدید
- باگ → تست regression
- refactor → تست‌های موجود باید پاس شوند

### ممنوع

- ❌ commit بدون تست (برای کد جدید)
- ❌ حذف تست بدون دلیل
- ❌ skip کردن تست بدون توضیح

---

## 📌 خلاصه

**۱۰ قاعده والکس:**

۱. قبل و بعد از هر تغییر، شاهد بگیر
۲. برای تغییرات حساس، Python (نه sed)
۳. ابزار مناسب برای کار مناسب
۴. commit‌های atomic با پیام واضح
۵. git add -p، نه git add -A
۶. فایل markdown ≤ ۳۰۰ خط
۷. ساختار مسطح docs/ + پوشه‌های موضوعی
۸. همه چیز را بازبینی کن (دی + نووآ + حسین)
۹. معماری DDD + Hexagonal — وابستگی به Domain
۱۰. هر تغییر کد، حداقل یک تست

---

## 📚 مراجع

- **اصول AI:** `AI_PRIMER.md` (روت)
- **شروع کار:** `docs/GETTING_STARTED.md`
- **معماری:** `docs/ARCHITECTURE.md`
- **راه‌اندازی:** `docs/SETUP.md`
- **API:** `docs/API.md`
- **ربات‌ها:** `docs/BOTS.md`

---

**«آهسته، مطمئن، با شاهد، با بازبینی.»** — SGPR (سرو پایا رشد سبز)

**موفق باشی، همراه.** 🌿
