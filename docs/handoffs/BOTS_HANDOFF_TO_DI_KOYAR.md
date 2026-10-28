# 🤖 Handoff: Robots (Bots) — From Di Parto to Di Koyar

- **تاریخ:** 2026-10-28
- **از:** دی پرتو (معمار فنی)
- **به:** دی کویر (مسئول ربات‌ها)
- **وضعیت:** All 263 unit tests pass. No known bugs.

---

## 🎯 وضعیت کلی ربات‌ها (آخرین شاهد)

| ربات | Tier | وضعیت |
|---|---|---|
| `nooaah` (نوح) | Production | ✅ سالم. تست‌های معماری (BaseBot) در بلاک ۱۰۹. |
| `bear_hunter` (شکارچی خرس) | Production | ✅ سالم. audit.py fix شده (بلاک ۱۲۴-۱۲۵). |
| `scalp_master` (اسکالپ مستر) | Production | ✅ سالم. از BaseBot ارث‌بری می‌کند. |
| `trend_follow`, `volatility_hunter`, `volatility_hunter_v2`, `mean_revert`, `grid_bot`, `smart_portfolio` | Experimental | ✅ سالم. تست نشده‌اند در production. |

---

## 🔍 شاهدهای مهم (برای شروع دی کویر)

### ۱. معماری
- همه‌ی ربات‌ها از `BaseBot` ارث‌بری می‌کنند.
- `BotRegistry` (singleton) همه‌ی ربات‌ها را ثبت می‌کند.
- API: `GET /v1/bots/list` (فیلتر بر اساس tier).
- `NooaahBot` به `BaseBot` متصل شده (بلاک ۱۰۹).

### ۲. Performance
- `Nooaah` cycle time: **۲.۵ms** (بدون I/O) — فوق‌العاده بهینه.
- `Bear Hunter`: I/O-bound (per-trade audit، نه per-tick).
- **گلوگاه واقعی:** والکس (که با `MarketsCache` و `CandlesCache` حل شده).

### ۳. امنیت
- `.env` با **۶۰۰** محافظت می‌شود (owned by deploy).
- توکن‌های والکس با **Fernet (AES-128-CBC + HMAC-SHA256)** رمزنگاری شده‌اند.
- ستون‌های `users.wallex_token_encrypted` و `users.wallex_trade_token_encrypted` (bytea/text).

### ۴. Audit Trail (Bear Hunter)
- `audit.py` — WAL pattern (write-ahead log) برای ترید.
- `log_trade_intent` قبل از ترید، `log_trade_success/failure` بعد.
- `audit.path` — حالا absolute (از `paths.DATA_DIR`).

### ۵. تست‌ها
- `pytest tests/unit/` → **۲۶۳ تست پاس**.
- تست‌های مربوط به ربات‌ها: `test_bot_architecture.py`, `test_bear_hunter_audit.py`.
- برای اجرا: `cd backend && source .venv/bin/activate && pytest tests/unit/ -q`

---

## 🚧 بدهی‌های فنی (پیشنهاد به دی کویر)

1. **`pre_flight.py`:** ۲۰+ چک در ۵ فاز. شاید بعضی چک‌ها قابل merge باشند (کاهش پیچیدگی).
2. **`Scalp Master`:** تست‌های integration (paper mode) ندارد.
3. **`Nooaah`:** استراتژی ML روی `backtest` نیاز به بازبینی دارد.
4. **`experimental bots`:** هیچ‌کدام تست integration ندارند.

---

## 📋 پیشنهاد اولویت دی کویر

1. **اول:** بررسی `bear_hunter` در production (آیا در حال ترید است؟).
2. **دوم:** تست `scalp_master` در paper mode (شاهد از عملکرد).
3. **سوم:** بررسی `nooaah` در production (آیا ML درست کار می‌کند؟).
4. **چهارم:** ربات‌های experimental (فقط برای تست، نه production).

---

## 🌿 شعار

**«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»**

— دی پرتو، معمار فنی
