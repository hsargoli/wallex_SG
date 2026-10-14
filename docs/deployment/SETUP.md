# Wallex Deployment — داستان ساخت

> این سند، روایت ساخت deployment Wallex روی سرور ـه.
> از صفر تا `sarvbots.ir` زنده.
> برای معماری نهایی، `README.md` رو ببین.

**تاریخ:** 2026-10-13 تا 2026-10-14
**مدت:** دو روز کاری
**نتیجه:** `sarvbots.ir` زنده، با HTTPS، Basic Auth، و Nooaah در حالت `killed`

---

## 📋 خلاصه

| فاز | کار | چالش اصلی |
|------|------|-----------|
| ۰ | آماده‌سازی سرور | Python 3.12 نبود، PPA تحریم بود |
| ۱ | نصب uv | astral.sh تحریم، RPM glibc نداشت |
| ۲ | clone Wallex | GitHub تحریم، scp از لوکال |
| ۳ | نصب dependencies | pip به PyPI بین‌الملل timeout، میرور داخلی |
| ۴ | backend systemd | — |
| ۵ | فرانت build | npm registry بین‌الملل timeout |
| ۶ | فرانت systemd | — |
| ۷ | nginx + دامنه | heredoc خراب شد، Python replace |
| ۸ | آروان SSL | Origin protocol، HTTPS اجبار |
| ۹ | Basic Auth | htpasswd، nginx reload |

---

## 🖥️ مشخصات سرور

| مورد | مقدار |
|------|-------|
| Hostname | fastcreate-691975 |
| OS | Ubuntu 22.04.5 LTS |
| IP | 87.248.152.239 |
| SSH Port | 9011 (نه 22) |
| RAM | 3.8GB |
| Disk | 20GB |
| Swap | 2GB |
| Node | v20.18.1 (از قبل نصب) |
| Python | 3.10.12 (سیستم) — 3.12.0 (کامپایل شده) |

**پروژه‌های دیگه (دست نزن!):**
- noosharp (8000 + 3000)
- mabacheha (8012)
- nourin / hosg.ir (8015)

---

## 📌 فاز ۰ — آماده‌سازی سرور

### مشکل: Python 3.12 نبود

Wallex به Python 3.12 نیاز داشت، ولی Ubuntu 22.04 فقط 3.10 داشت.

**راه اول — PPA deadsnakes:**
```bash
add-apt-repository ppa:deadsnakes/ppa -y
```
**نتیجه:** ❌ `TimeoutError: [Errno 110] Connection timed out` — چون `launchpad.net` از ایران تحریمه.

**راه دوم — uv python install:**
نیاز به uv داشت، که خودش نصب نبود.

**راه سوم — کامپایل از سورس (نتیجه‌ی نهایی):**

روی **لپ‌تاپ** دانلود شد (چون سرور به python.org دسترسی نداشت):
```bash
# 💻 لوکال
cd /tmp
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
scp -P 9011 Python-3.12.0.tgz root@87.248.152.239:/tmp/
```

روی **سرور**، پیش‌نیازها نصب و کامپایل شد:
```bash
# 🖥️ سرور (root)
apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
  libnss3-dev libssl-dev libreadline-dev libffi-dev libbz2-dev \
  libsqlite3-dev wget curl
cd /tmp
tar -xf Python-3.12.0.tgz
cd Python-3.12.0
./configure --enable-optimizations --prefix=/usr/local
make -j$(nproc)
make altinstall   # نه install — تا Python 3.10 سیستم دست نخوره
```

**نتیجه:** ✅ `/usr/local/bin/python3.12` — Python 3.12.0

**درس:** `altinstall` باعث شد Python سیستم (3.10) دست نخوره. پروژه‌های دیگه (noosharp، mabacheha) که با 3.10 کار می‌کنن، آسیب ندن.

---

## 📌 فاز ۱ — نصب uv

### مشکل: astral.sh تحریم

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
**نتیجه:** ❌ `Connection timed out`

**راه دوم — GitHub Releases:**
```bash
curl -LsSf https://github.com/astral-sh/uv/releases/... | tar xzf - -C /usr/local/bin
```
**نتیجه:** ❌ `Connection timed out` — GitHub هم تحریم.

**راه سوم — RPM از مبین‌هاست:**
```bash
curl -LO https://mirror.mobinhost.com/epel/10/Everything/x86_64/Packages/u/uv-0.12.7-3.el10_3.x86_64.rpm
rpm2cpio uv-0.12.7-3.el10_3.x86_64.rpm | cpio -idmv
/tmp/usr/bin/uv --version
```
**نتیجه:** ❌ `GLIBC_2.39' not found` — RPM برای RHEL 10 بود، glibc 2.39 می‌خواست، Ubuntu 22.04 glibc 2.35 داره.

**راه چهارم — wheel از PyPI میرور داخلی (نتیجه‌ی نهایی):**

اول میرورهای PyPI داخلی تست شدن. کارگدان `uv` رو داشت، ولی ناقص. آروان 503 داد. **Runflare** کار کرد:

```bash
# 🖥️ سرور (deploy)
cd /home/deploy/wallex/backend
/usr/local/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install uv \
  --index-url https://mirror-pypi.runflare.com/simple \
  --trusted-host mirror-pypi.runflare.com
uv --version
```

**نتیجه:** ✅ `uv 0.12.23`

**درس:** قانون ۱۴ AI_PRIMER: «library که ۲ بار شکست خورد، ابزار رو عوض کن.» ما ۳ بار عوض کردیم: PPA → uv → RPM → **wheel از Runflare**.

---

## 📌 فاز ۲ — clone Wallex

### مشکل: GitHub تحریم

سرور به GitHub دسترسی نداشت. پس **`scp` از لوکال:**

```bash
# 💻 لوکال
cd ~/wallex
# حذف پوشه‌های حجیم (قابل بازسازی)
rm -rf backend/.venv frontend/node_modules frontend/.next
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# انتقال (فقط کد + .git)
cd ~
scp -P 9011 -r wallex root@87.248.152.239:/tmp/
```

**نتیجه:** ✅ ۳۱MB به‌جای ۱.۲GB (چون `.venv`، `node_modules`، `.next` حذف شدن)

روی **سرور**، انتقال به مسیر نهایی:
```bash
# 🖥️ سرور (root)
mv /tmp/wallex /home/deploy/wallex
chown -R deploy:deploy /home/deploy/wallex
```

**درس:** `.venv`، `node_modules`، `.next` روی سرور از نو ساخته می‌شن — چون برای معماری سرور build می‌شن، نه لپ‌تاپ.

---

## 📌 فاز ۳ — نصب dependencies

### مشکل: pip به PyPI بین‌الملل timeout

```bash
pip install -e .
```
**نتیجه:** ❌ `[Errno 101] Network is unreachable` — pip سعی کرد از PyPI بین‌الملل بگیره.

**راه‌حل — uv با میرور داخلی:**

```bash
# 🖥️ سرور (deploy)
cd /home/deploy/wallex/backend
uv sync --python 3.12 \
  --index-url https://mirror-pypi.runflare.com/simple \
  --default-index https://mirror-pypi.runflare.com/simple
```

**نتیجه‌ی اول:** ❌ `scikit-learn: I/O operation failed during extraction`

**راه‌حل — پاک کردن cache uv:**
```bash
rm -rf /home/deploy/.cache/uv/
rm -rf /tmp/Python-3.12.0
rm -f /tmp/Python-3.12.0.tgz
```

**نتیجه‌ی دوم:** ✅ `Installed 64 packages in 330ms`

**درس:** cache uv می‌تونه خراب شه. پاک کردنش، مشکل رو حل می‌کنه.

---

## 📌 فاز ۴ — backend systemd

**فایل `/etc/systemd/system/wallex-backend.service`:**

```ini
[Unit]
Description=Wallex Nooaah Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/wallex/backend
EnvironmentFile=/home/deploy/wallex/.env
ExecStart=/home/deploy/wallex/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8020 --workers 1
Restart=always
RestartSec=10
StandardOutput=append:/var/log/wallex-backend.log
StandardError=append:/var/log/wallex-backend.log

[Install]
WantedBy=multi-user.target
```

**نکته‌ها:**
- `EnvironmentFile=/home/deploy/wallex/.env` — مسیر `.env` که از `ROOT_DIR` خونده می‌شه
- `User=deploy` + `Group=deploy` — نه root
- `Restart=always` — اگه crash کرد، خودکار بالا میاد
- `127.0.0.1:8020` — نه `0.0.0.0` (nginx بعداً reverse proxy می‌کنه)

**فعال‌سازی:**
```bash
systemctl daemon-reload
systemctl enable wallex-backend
systemctl start wallex-backend
```

---

## 📌 فاز ۵ — فرانت build

### مشکل: npm registry بین‌الملل timeout

```bash
npm install
```
**نتیجه:** ❌ `E500` روی `@radix-ui/react-menubar` — میرور کارگدان ناقص.

**راه‌حل — Runflare:**
```bash
npm config set registry https://mirror-npm.runflare.com
npm install
```
**نتیجه:** ✅ `added 679 packages, and audited 680 packages in 1m`

**build:**
```bash
npm run build
```
**نتیجه:** ✅ `Compiled successfully in 33.7s` — ۲۱ route

**درس:** npm هم مثل PyPI، میرور داخلی لازم داره. Runflare هر دو رو داره.

---

## 📌 فاز ۶ — فرانت systemd

**فایل `/etc/systemd/system/wallex-frontend.service`:**

```ini
[Unit]
Description=Wallex Nooaah Frontend (Next.js)
After=network.target wallex-backend.service
Wants=wallex-backend.service

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/wallex/frontend
EnvironmentFile=/home/deploy/wallex/frontend/.env.local
ExecStart=/usr/bin/npm run start -- --port 3020
Restart=always
RestartSec=10
StandardOutput=append:/var/log/wallex-frontend.log
StandardError=append:/var/log/wallex-frontend.log

[Install]
WantedBy=multi-user.target
```

**نکته:** `After=wallex-backend.service` + `Wants=wallex-backend.service` — فرانت بعد از backend بالا میاد.

---

## 📌 فاز ۷ — nginx + دامنه

### مشکل: heredoc خراب شد

اول با heredoc ساخته شد، ولی خط آخر قاطی شد:
```
WALLEX_NGINX_EOFnd_timeout 3600s;ded-Proto $scheme;_x_forwarded_for;
```

**راه‌حل — Python replace (طبق AI_PRIMER):**
```bash
python3 << 'PYEOF'
from pathlib import Path

content = '''...'''
p = Path('/etc/nginx/sites-available/wallex')
p.write_text(content, encoding='utf-8')
PYEOF
```

**درس:** برای فایل‌های حساس، Python replace امن‌تر از heredocـه.

**فایل نهایی `/etc/nginx/sites-available/wallex`:**

سه location:
- `/` → `http://127.0.0.1:3020` (frontend)
- `/api/backend/*` → `http://127.0.0.1:8020/` (backend, از فرانت)
- `/api/*` → `http://127.0.0.1:8020/` (backend, direct)
- `/ws/*` → `http://127.0.0.1:8020/ws/` (WebSocket)

**⚠️ نکته‌ی مهم:** قبل از reload، `nginx -t` و **بکاپ از `/etc/nginx/nginx.conf`**.

---

## 📌 فاز ۸ — آروان SSL

**تنظیمات آروان:**

| مورد | مقدار |
|------|-------|
| NS | d.ns.arvancdn.ir, v.ns.arvancdn.ir |
| رکورد A | sarvbots.ir → IP آروان |
| Origin | http://87.248.152.239:80 |
| SSL | فعال (Let's Encrypt رایگان) |
| HTTPS اجباری | فعال |
| پروتکل Origin | **HTTP** (نه HTTPS) |

**⚠️ نکته:** «ارتباط با سرورهای اصلی» باید **HTTP** باشه، نه «خودکار» — چون nginx روی سرور فقط HTTP گوش می‌ده.

**درس:** اگه «خودکار» انتخاب بشه، آروان ممکنه HTTPS تلاش کنه → 502 Bad Gateway.

---

## 📌 فاز ۹ — Basic Auth

**نصب htpasswd:**
```bash
apt install -y apache2-utils
htpasswd -c /etc/nginx/.htpasswd_wallex hosein
```

**اضافه کردن به nginx:**
```nginx
auth_basic "Wallex — Restricted";
auth_basic_user_file /etc/nginx/.htpasswd_wallex;
```

**درس:** Basic Auth روی nginx، ساده‌ترین راه محدود کردن دسترسیـه. برای امنیت بیشتر، IP Whitelist توی آروان هم می‌شه اضافه کرد.

---

## 📌 امنیت Nooaah

**تنظیمات فعلی:**

| متغیر | مقدار |
|-------|-------|
| `LIVE_TRADING_ENABLED` | False |
| `killed` | true |
| `mode` | live-paused |

**یعنی:** Nooaah معامله نمی‌کنه، ولی به والکس وصلـه (برای نمایش).

**⚠️ نکته:** توکن فعلی، توکن شخصی حسینه. برای production، باید یه توکن جداگانه (فقط خواندنی) ساخته شه.

---

## 🎓 درس‌های کلیدی

**۱. تحریم، راه‌حل داره.**
PPA نبود → سورس کامپایل. astral.sh نبود → wheel از Runflare. GitHub نبود → scp.

**۲. میرورهای داخلی رو بشناس.**
Runflare برای PyPI و npm. کارگدان ناقصه. آروان گاهی 503 می‌ده.

**۳. `altinstall` برای Python.**
تا Python سیستم (3.10) دست نخوره — پروژه‌های دیگه آسیب ندن.

**۴. فایل‌های حجیم رو انتقال نده.**
`.venv`، `node_modules`، `.next` روی سرور از نو ساخته می‌شن.

**۵. قبل از nginx، بکاپ.**
`cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak.$(date +%Y%m%d_%H%M%S)`

**۶. Python replace برای فایل‌های حساس.**
heredoc ممکنه خراب شه (مخصوصاً با یونیکد فارسی).

**۷. `LIVE_TRADING_ENABLED=False` لایه‌ی امنیت.**
حتی اگه کسی `resume` بزنه، معامله نمی‌کنه.

**۸. پروژه‌های دیگه، خط سرخ.**
هیچ فایل مشترکی دست نخورد. هیچ دامنه‌ای تغییر نکرد.

---

## 🔗 لینک‌های مرتبط

- [`README.md`](./README.md) — معماری deployment
- [`OPERATIONS.md`](./OPERATIONS.md) — راهنمای روزمره
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — معماری کد

---

**آخرین آپدیت:** 2026-10-14
**نسخه:** 1.0
