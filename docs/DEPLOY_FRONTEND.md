# 🚀 راهنمای دیپلوی فرانت‌اند (Frontend Deploy Guide)

> **هدف:** استقرار کدهای جدید فرانت‌اند (Next.js) روی سرور production (sarvbots.ir).
> **مخاطب:** هر دی (AI) یا مهندسی که مسئول deploy است.

---

## 📋 پیش‌نیازها
- دسترسی SSH به سرور (`ssh -p 9011 root@87.248.152.239`)
- سرویس `wallex-frontend` روی سرور فعال باشد.
- پوشه‌ی `/home/deploy/wallex/frontend/` وجود داشته باشد.

---

## 🛠️ روش ۱ — استاندارد (rsync + build + restart) — **توصیه‌شده**

این روش امن‌تر است چون فایل‌های اضافی (مثل `.next` قدیمی) را پاک می‌کند و وابسته به git روی سرور نیست.

### ۱. Dry-run (اجباری — طبق M22)
```bash
cd ~/wallex
rsync -avzn --delete \
  --exclude='node_modules' --exclude='.next' \
  --exclude='.env.local' --exclude='.env' \
  --exclude='.git' --exclude='tsconfig.tsbuildinfo' \
  -e "ssh -p 9011" \
  frontend/ root@87.248.152.239:/home/deploy/wallex/frontend/

چک کن: خروجی deleting نباید چیزی غیرمنتظره نشان دهد.
۲. rsync واقعی (بدون -n)
bash

cd ~/wallex
rsync -avz --delete \
  --exclude='node_modules' --exclude='.next' \
  --exclude='.env.local' --exclude='.env' \
  --exclude='.git' --exclude='tsconfig.tsbuildinfo' \
  -e "ssh -p 9011" \
  frontend/ root@87.248.152.239:/home/deploy/wallex/frontend/

۳. chown + build + restart
bash

ssh -p 9011 root@87.248.152.239 "chown -R deploy:deploy /home/deploy/wallex/frontend && \
  su - deploy -c 'cd /home/deploy/wallex/frontend && npm run build' && \
  systemctl restart wallex-frontend"

🛠️ روش ۲ — سریع (git pull + build + restart) — فقط اگر سرور مخزن git دارد

اگر روی سرور یک مخزن git clone شده دارید (در /home/deploy/wallex/)، می‌توانید از این روش استفاده کنید.
۱. pull
bash

ssh -p 9011 root@87.248.152.239 "su - deploy -c 'cd ~/wallex && git pull origin refactor/full-ddd'"

۲. build + restart
bash

ssh -p 9011 root@87.248.152.239 "su - deploy -c 'cd ~/wallex/frontend && npm run build' && sudo systemctl restart wallex-frontend"

    ⚠️ نکته: git pull ممکن است با تغییرات محلی تداخل کند. قبل از pull، مطمئن شو git status روی سرور تمیز است.

🧪 شاهد بعد از Deploy
تست مستقیم روی سرور (با Host Header)
bash

ssh -p 9011 root@87.248.152.239 "curl -s -H 'Host: sarvbots.ir' -o /dev/null -w 'terms: HTTP %{http_code}\n' http://127.0.0.1/terms"

تست از دامنه (با دور زدن کش ArvanCloud)
bash

curl -sI "https://sarvbots.ir/terms?v=999" | grep -iE "HTTP/|x-nextjs-cache"

انتظار: HTTP/2 200 و x-nextjs-cache: HIT یا MISS.
اگر ۴۰۴ گرفتی:

    احتمال ۱: کش ArvanCloud قدیمی است. باید از پنل ArvanCloud → CDN → Purge Cache را بزنی.

    احتمال ۲: Nginx به سرویس اشتباهی (مثلاً پورت ۳۰۰۰) پروکسی می‌کند. کانفیگ Nginx را چک کن: grep -n "proxy_pass" /etc/nginx/sites-available/wallex.

    احتمال ۳: فایل‌های build روی سرور وجود ندارند. با ls -la /home/deploy/wallex/frontend/.next/server/app/ چک کن.

🔧 عیب‌یابی سریع (Troubleshooting)
مشکل	علت احتمالی	راه‌حل
404 روی دامنه ولی 200 روی localhost:3020	کش ArvanCloud / Nginx	Purge کش + چک Nginx
502 Bad Gateway	سرویس frontend down	systemctl status wallex-frontend + journalctl -u wallex-frontend
npm run build خطا می‌دهد	خطای TypeScript یا وابستگی	cd frontend && npm install && npx tsc --noEmit
فایل‌های جدید در build نیستند	rsync اشتباه / build قدیمی	دوباره rsync + build
📝 چک‌لیست قبل از Deploy

    □

    git status تمیز است.
    □

    آخرین commit را git log --oneline -1 چک کردی.
    □

    Dry-run rsync را دیدی.
    □

    npm run build را لوکال تست کردی (اختیاری ولی توصیه‌شده).
    □

    بعد از deploy، شاهد curl را گرفتی.

🔗 لینک‌های مرتبط

    AI_PRIMER.md — قانون M21 (tag قبل از deploy)، M22 (dry-run)

    docs/adr/0024-paper-mode-success.md — قوانین deploy

آهسته، با شاهد، مطمئن.
