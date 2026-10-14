# Wallex Deployment — معماری

> این سند، معماری deployment Wallex (Nooaah) روی سرور رو توضیح می‌ده.
> برای داستان ساخت، `SETUP.md` رو ببین.
> برای کارهای روزمره، `OPERATIONS.md` رو ببین.

---

## 📍 نگاه کلی

| مورد | مقدار |
|------|-------|
| **دامنه** | `sarvbots.ir` |
| **سرور** | `87.248.152.239` (SSH پورت `9011`) |
| **Hostname** | `fastcreate-691975` |
| **OS** | Ubuntu 22.04.5 LTS |
| **مسیر پروژه** | `/home/deploy/wallex` |
| **کاربر سرویس** | `deploy` (نه root) |
| **ریپو** | `git@github.com:hsargoli/wallex_SG.git` |
| **برنچ** | `refactor/full-ddd` |
| **CDN** | ابرآروان (DNS + SSL + DDoS) |

---

## 🏗️ معماری

```
کاربر (مرورگر)
    ↓ HTTPS
[آروان: DNS + SSL + DDoS]
    ↓ HTTP (Origin)
[سرور: 87.248.152.239:80]
    ↓
[nginx: sarvbots.ir]
    ├── /              → frontend (127.0.0.1:3020)
    ├── /api/backend/* → backend  (127.0.0.1:8020)
    ├── /api/*         → backend  (127.0.0.1:8020)
    └── /ws/*          → backend  (127.0.0.1:8020, WebSocket)
```

**نکته:** آروان SSL رو terminate می‌کنه (کاربر ↔ آروان = HTTPS، آروان ↔ سرور = HTTP).

---

## 🔧 سرویس‌ها (systemd)

| سرویس | فایل | کاربر | پورت | وضعیت |
|-------|------|-------|------|-------|
| `wallex-backend` | `/etc/systemd/system/wallex-backend.service` | `deploy` | `127.0.0.1:8020` | enabled + active |
| `wallex-frontend` | `/etc/systemd/system/wallex-frontend.service` | `deploy` | `*:3020` | enabled + active |

**وابستگی:** `wallex-frontend` بعد از `wallex-backend` بالا میاد (`After=` + `Wants=`).

**لاگ‌ها:**
- `/var/log/wallex-backend.log`
- `/var/log/wallex-frontend.log`

---

## 🌐 دامنه و SSL (آروان)

| مورد | مقدار |
|------|-------|
| **NS** | `d.ns.arvancdn.ir`, `v.ns.arvancdn.ir` |
| **رکورد A** | `sarvbots.ir` → IP آروان (`185.143.233.132`, `185.143.234.132`) |
| **Origin** | `http://87.248.152.239:80` |
| **SSL** | فعال (Let's Encrypt رایگان آروان) |
| **HTTPS اجباری** | فعال (HTTP → HTTPS) |
| **پروتکل Origin** | HTTP (نه HTTPS) |

---

## 🔐 امنیت

| لایه | وضعیت |
|------|-------|
| **Basic Auth (nginx)** | فعال — `/etc/nginx/.htpasswd_wallex` |
| **HTTPS** | فعال (آروان) |
| **`LIVE_TRADING_ENABLED`** | `False` — معامله‌ی واقعی خاموش |
| **`killed`** | `true` — scheduler متوقف |
| **`mode`** | `live-paused` |

**نکته:** توکن فعلی، توکن شخصی حسینه. برای production، باید یه توکن جداگانه (فقط خواندنی) ساخته شه.

---

## 📂 مسیرهای nginx

فایل: `/etc/nginx/sites-available/wallex` (لینک توی `sites-enabled/`)

| مسیر | مقصد | توضیح |
|------|------|-------|
| `/` | `http://127.0.0.1:3020` | frontend (Next.js) |
| `/api/backend/*` | `http://127.0.0.1:8020/` | backend (frontend requests) |
| `/api/*` | `http://127.0.0.1:8020/` | backend (direct) |
| `/ws/*` | `http://127.0.0.1:8020/ws/` | WebSocket (ticker) |

**Basic Auth:** روی همه‌ی مسیرها (`auth_basic` توی server block).

---

## 🐍 وابستگی‌ها

| ابزار | نسخه | نصب از |
|-------|------|--------|
| Python | 3.12.0 | کامپایل از سورس (`/usr/local/bin/python3.12`) |
| Node.js | v20.18.1 | از قبل روی سرور |
| npm | 10.8.2 | همراه Node |
| uv | 0.12.23 | wheel از Runflare (`pip install uv`) |

**میرورها:**
- **PyPI:** `https://mirror-pypi.runflare.com/simple`
- **npm:** `https://mirror-npm.runflare.com`

**چرا این‌ها؟** چون astral.sh، github.com، و pypi.org از ایران تحریم‌ان. (جزئیات توی `SETUP.md`)

---

## 📊 منابع سرور

| مورد | مقدار |
|------|-------|
| **RAM** | ۳.۸GB (۲.۶GB آزاد) |
| **Disk** | ۲۰GB (۶GB آزاد — ۶۸٪ استفاده) |
| **Swap** | ۲GB |

**پروژه‌های دیگه روی سرور (دست نزن!):**
- `noosharp` → `/var/www/noosharp`، پورت ۸۰۰۰ + ۳۰۰۰
- `mabacheha` → `/var/www/mabacheha`، پورت ۸۰۱۲
- `nourin` (hosg.ir) → `/var/opt/nourin`، پورت ۸۰۱۵

---

## 🔗 لینک‌های مرتبط

- [`SETUP.md`](./SETUP.md) — داستان ساخت (برای دی بعدی)
- [`OPERATIONS.md`](./OPERATIONS.md) — راهنمای روزمره (restart, logs, backup)
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — معماری کد (DDD, Hexagonal)
- [`../AI_PROJECT_GUIDE.md`](../AI_PROJECT_GUIDE.md) — راهنمای AI

---

**آخرین آپدیت:** 2026-10-14
**نسخه:** 1.0
