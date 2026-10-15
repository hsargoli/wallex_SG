# Wallex Deployment — مسائل شناخته‌شده

> این سند، مسائل شناخته‌شده‌ی deployment رو ثبت می‌کنه.
> برای معماری، `README.md` رو ببین.

**آخرین آپدیت:** 2026-10-15

---

## KI-001: WebSocket از طریق آروان کار نمی‌کند

**وضعیت:** 🔴 باز
**تصمیم:** ⏸️ رها شده برای MVP — در فاز بعدی حل می‌شود
**تأثیر:** 🟡 آپدیت لحظه‌ای قیمت کار نمی‌کند (بقیه‌ی داده‌ها از API می‌آید)

### علت

آروان، WebSocket را روی HTTP/2 پشتیبانی نمی‌کند (404 برمی‌گرداند). روی HTTP/1.1 کار می‌کند (تست curl تأیید کرد)، ولی:

- مرورگرها معمولاً برای WebSocket، HTTP/2 را انتخاب می‌کنند
- پنل آروان، گزینه‌ی خاموش کردن HTTP/2 را ندارد
- VPN روی بعضی مرورگرها هم اثر دارد (تست شد، مشکل بود)

### شواهد

**تست curl از سرور:**

```bash
# HTTP/2 → 404 (server: ArvanCloud)
curl -sv --http2 -H "Upgrade: websocket" ... https://sarvbots.ir/ws/ticker/BTCTMN

# HTTP/1.1 → 101 Switching Protocols (کار می‌کند)
curl -sv --http1.1 -H "Upgrade: websocket" ... https://sarvbots.ir/ws/ticker/BTCTMN
```

**تست مستقیم backend (بدون آروان):**
- `ws://127.0.0.1:8020/ws/ticker/BTCTMN` → ✅ OK

**تست مستقیم nginx (بدون آروان):**
- `ws://127.0.0.1/ws/ticker/BTCTMN` (با Host: sarvbots.ir) → ✅ 101 Switching Protocols

**تست مرورگر (Firefox):**
- `wss://sarvbots.ir/ws/ticker/BTCTMN` → ❌ CONNECTION_REFUSED

### نتیجه‌گیری

backend و nginx سالمه. مشکل فقط آروان است.

### راه‌حل‌های ممکن (فاز بعدی)

| # | راه‌حل | زمان | توضیح |
|---|--------|------|-------|
| ۱ | **Polling در frontend** (برای MVP) | ۱۰ دقیقه | هر ۵ ثانیه API call |
| ۲ | **ساب‌دامین بدون CDN** (`ws.sarvbots.ir`) | ۲۰ دقیقه | A record مستقیم + SSL جداگانه |
| ۳ | **تماس با پشتیبانی آروان** | ۱-۳ روز | ممکن است HTTP/2 را خاموش کنند |
| ۴ | **CDN دیگه** | چند روز | هزینه + migration |

**تصمیم MVP:** راه‌حل ۱ (polling) — ساده، سریع.

---

## KI-002: API timeout روی `/v1/signals/batch`

**وضعیت:** 🟡 جزئی
**تأثیر:** 🟡 batch signals خالی برمی‌گردد

### علت

Wallex API برای ۱۰ نماد کند پاسخ می‌دهد (هر نماد ~۸ ثانیه). `WALLEX_TIMEOUT_SECONDS=30` کافی نبود.

### راه‌حل موقت

- Background job (scheduler) هر ۵ دقیقه batch را fetch کند
- یا cache نتیجه

**برای MVP:** فقط ignore — صفحه‌های دیگر کار می‌کنند.

---

## KI-003: API 500 روی `/v1/account/cost-basis` و `/v1/orders`

**وضعیت:** 🔴 باز
**تأثیر:** 🟡 داشبورد، این دو بخش را لود نمی‌کند

### علت

احتمالاً:
- توکن والکس منقضی شده
- rate limit والکس
- timeout (۳۰s کافی نبود)

### راه‌حل موقت

- چک توکن
- timeout = 60s
- یا cache

**برای MVP:** فقط ignore.

---

## 🔗 لینک‌های مرتبط

- [`README.md`](./README.md) — معماری deployment
- [`SETUP.md`](./SETUP.md) — داستان ساخت
- [`OPERATIONS.md`](./OPERATIONS.md) — راهنمای روزمره

---

**آخرین آپدیت:** 2026-10-15
**نسخه:** 1.0
