# Wallex Deployment — راهنمای عملیات

> این سند، راهنمای کارهای روزمره روی Wallex deploymentـه.
> برای معماری، `README.md` رو ببین.
> برای داستان ساخت، `SETUP.md` رو ببین.

---

## 🚀 restart سرویس‌ها

### backend

**🖥️ سرور (root):**
```bash
systemctl restart wallex-backend
systemctl is-active wallex-backend
```

### frontend

**🖥️ سرور (root):**
```bash
systemctl restart wallex-frontend
systemctl is-active wallex-frontend
```

### هر دو با هم

**🖥️ سرور (root):**
```bash
systemctl restart wallex-backend wallex-frontend
systemctl is-active wallex-backend wallex-frontend
```

---

## 📜 دیدن log

### backend (real-time)

**🖥️ سرور (root):**
```bash
tail -f /var/log/wallex-backend.log
```

### frontend (real-time)

**🖥️ سرور (root):**
```bash
tail -f /var/log/wallex-frontend.log
```

### systemd journal

**🖥️ سرور (root):**
```bash
journalctl -u wallex-backend -n 50 --no-pager
journalctl -u wallex-frontend -n 50 --no-pager
```

### nginx

**🖥️ سرور (root):**
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 🔍 چک سلامت

### backend

**🖥️ سرور (root):**
```bash
curl -s http://127.0.0.1:8020/health
curl -s http://127.0.0.1:8020/v1/nooaah/config | python3 -m json.tool | grep -E "mode|killed"
```

### frontend

**🖥️ سرور (root):**
```bash
curl -sI http://127.0.0.1:3020 2>&1 | head -1
```

### از بیرون (با دامنه)

**💻 لوکال (hosein):**
```bash
curl -sI https://sarvbots.ir 2>&1 | head -1
# انتظار: 401 (چون Basic Auth)
```

### پروژه‌های دیگه (مهم!)

**🖥️ سرور (root):**
```bash
curl -sI http://noosharp.ir 2>&1 | head -1
curl -sI http://mabacheha.ir 2>&1 | head -1
curl -sI http://hsgh.ir 2>&1 | head -1
```

**⚠️ هر بار بعد از تغییر nginx، اینا رو چک کن.**

---

## 💾 backup

### state Nooaah

**🖥️ سرور (root):**
```bash
# state.json
cp /home/deploy/wallex/backend/data/nooaah/state.json \
   /home/deploy/wallex/backend/data/nooaah/state.json.bak.$(date +%Y%m%d_%H%M%S)

# لیست بکاپ‌ها
ls -la /home/deploy/wallex/backend/data/nooaah/
```

### `.env`

**🖥️ سرور (root):**
```bash
cp /home/deploy/wallex/.env \
   /home/deploy/wallex/.env.bak.$(date +%Y%m%d_%H%M%S)
```

### nginx config

**🖥️ سرور (root):**
```bash
cp /etc/nginx/sites-available/wallex \
   /etc/nginx/sites-available/wallex.bak.$(date +%Y%m%d_%H%M%S)
```

### systemd service

**🖥️ سرور (root):**
```bash
cp /etc/systemd/system/wallex-backend.service \
   /etc/systemd/system/wallex-backend.service.bak.$(date +%Y%m%d_%H%M%S)
```

---

## 🔐 تغییر توکن والکس

**مثلاً وقتی می‌خوای از توکن شخصی به توکن Nooaah (فقط خواندنی) سوییچ کنی:**

**۱. توی پنل والکس، API-Key جدید بساز (فقط خواندنی)**

**۲. 🖥️ سرور (root):**
```bash
# بکاپ
cp /home/deploy/wallex/.env /home/deploy/wallex/.env.bak.$(date +%Y%m%d_%H%M%S)

# ویرایش
nano /home/deploy/wallex/.env
# WALLEX_API_KEY رو با توکن جدید عوض کن
```

**۳. restart:**
```bash
systemctl restart wallex-backend
sleep 5
systemctl is-active wallex-backend
```

**۴. تست:**
```bash
curl -s http://127.0.0.1:8020/v1/account/balances 2>&1 | head -3
```

---

## 🔐 تغییر پسورد Basic Auth

**🖥️ سرور (root):**
```bash
# فقط پسورد hosein رو عوض کن (بدون -c)
htpasswd /etc/nginx/.htpasswd_wallex hosein

# اضافه کردن کاربر جدید
htpasswd /etc/nginx/.htpasswd_wallex user2

# حذف کاربر
htpasswd -D /etc/nginx/.htpasswd_wallex user2
```

**نکته:** nginx نیازی به reload نداره — htpasswd توی هر request خونده می‌شه.

**⚠️ `-c` رو استفاده نکن** — فایل رو از نو می‌سازه و کاربرای دیگه پاک می‌شن.

---

## 🚦 kill / resume Nooaah

### kill (متوقف کردن معاملات)

**🖥️ سرور (root):**
```bash
curl -X POST http://127.0.0.1:8020/v1/nooaah/kill
curl -s http://127.0.0.1:8020/v1/nooaah/config | python3 -m json.tool | grep -E "killed|mode"
# انتظار: killed: true, mode: live-paused
```

### resume (فعال کردن)

**⚠️ هشدار:** قبل از resume، مطمئن شو `LIVE_TRADING_ENABLED=False`ـه یا سرمایه/daily_limit درسته.

**🖥️ سرور (root):**
```bash
curl -X POST http://127.0.0.1:8020/v1/nooaah/resume
curl -s http://127.0.0.1:8020/v1/nooaah/config | python3 -m json.tool | grep -E "killed|mode"
```

---

## 🔄 به‌روزرسانی کد (از لوکال به سرور)

### کل چرخه

**۱. 💻 لوکال — تغییر بده:**
```bash
cd ~/wallex
# تغییرات رو بزن
git add .
git commit -m "feat: ..."
git push origin refactor/full-ddd
```

**۲. 💻 لوکال — انتقال با rsync:**

**فقط frontend:**
```bash
rsync -avz --delete \
  --exclude='node_modules' --exclude='.next' \
  --exclude='.env.local' --exclude='.env' \
  -e "ssh -p 9011" \
  ~/wallex/frontend/ \
  root@87.248.152.239:/home/deploy/wallex/frontend/
```

**فقط backend:**
```bash
rsync -avz --delete \
  --exclude='.venv' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.env' \
  -e "ssh -p 9011" \
  ~/wallex/backend/ \
  root@87.248.152.239:/home/deploy/wallex/backend/
```

**۳. 🖥️ سرور (root) — rebuild و restart:**
```bash
chown -R deploy:deploy /home/deploy/wallex/frontend /home/deploy/wallex/backend

# frontend: rebuild
su - deploy -c "cd /home/deploy/wallex/frontend && npm run build"

# restart
systemctl restart wallex-backend wallex-frontend
sleep 3
systemctl is-active wallex-backend wallex-frontend
```

---

## 🛠️ عیب‌یابی

### backend بالا نمیاد

**🖥️ سرور (root):**
```bash
systemctl status wallex-backend --no-pager
journalctl -u wallex-backend -n 50 --no-pager
tail -50 /var/log/wallex-backend.log
```

**خطاهای رایج:**
- `EnvironmentFile` پیدا نشد → `.env` جابه‌جا شده
- `Address already in use` → پورت 8020 اشغاله
- `ModuleNotFoundError` → venv ناقص

### frontend بالا نمیاد

**🖥️ سرور (root):**
```bash
systemctl status wallex-frontend --no-pager
tail -50 /var/log/wallex-frontend.log
```

**خطاهای رایج:**
- `.next` نیست → `npm run build` یادت رفته
- پورت 3020 اشغاله

### nginx خطا می‌ده

**🖥️ سرور (root):**
```bash
nginx -t
tail -50 /var/log/nginx/error.log
```

**⚠️ اگه `nginx -t` fail داد، reload نکن** — اول درستش کن.

### 502 Bad Gateway

**یعنی:** nginx به backend/frontend وصل نمی‌شه.

**راه‌حل:**
```bash
systemctl is-active wallex-backend wallex-frontend
ss -tlnp | grep -E "8020|3020"
```

### کاربر نمی‌تونه وارد شه (401)

**یعنی:** Basic Auth کار می‌کنه، ولی پسورد اشتباهه.

**راه‌حل:**
```bash
cat /etc/nginx/.htpasswd_wallex
# اگه کاربر نیست، اضافه کن
htpasswd /etc/nginx/.htpasswd_wallex hosein
```

---

## ⚠️ قوانین طلایی

**۱. قبل از تغییر nginx، بکاپ بگیر.**
```bash
cp /etc/nginx/sites-available/wallex /etc/nginx/sites-available/wallex.bak.$(date +%Y%m%d_%H%M%S)
```

**۲. بعد از هر تغییر، پروژه‌های دیگه رو چک کن:**
```bash
curl -sI http://noosharp.ir 2>&1 | head -1
curl -sI http://mabacheha.ir 2>&1 | head -1
curl -sI http://hsgh.ir 2>&1 | head -1
```

**۳. قبل از `nginx -t`، فایل رو ذخیره کن:**
```bash
nginx -t && systemctl reload nginx
```

**۴. هیچ‌وقت `git add -A` نزن.**
فایل خاص:
```bash
git add docs/deployment/OPERATIONS.md
```

**۵. `.env` رو از لوکال به سرور نبر.**
هر محیط `.env` خودش رو داره.

---

## 📞 در مواقع اضطراری

**اگه Nooaah معامله‌ی ناخواسته کرد:**

**🖥️ سرور (root):**
```bash
# فوری kill
curl -X POST http://127.0.0.1:8020/v1/nooaah/kill

# چک
curl -s http://127.0.0.1:8020/v1/nooaah/config | python3 -m json.tool | grep -E "killed|mode"
```

**اگه backend کرش کرد:**
```bash
systemctl restart wallex-backend
```

**اگه nginx کرش کرد:**
```bash
systemctl restart nginx
# ⚠️ این همه‌ی دامنه‌ها رو تحت تأثیر قرار می‌ده
```

---

## 🔗 لینک‌های مرتبط

- [`README.md`](./README.md) — معماری deployment
- [`SETUP.md`](./SETUP.md) — داستان ساخت
- [`../AI_PROJECT_GUIDE.md`](../AI_PROJECT_GUIDE.md) — راهنمای AI

---

**آخرین آپدیت:** 2026-10-14
**نسخه:** 1.0
