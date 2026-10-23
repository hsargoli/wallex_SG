# 🐻 Bear Hunter — گزارش جامع (نسخه ۲)

**تاریخ:** 2026-10-18 (عصر)
**Branch:** `refactor/full-ddd`
**HEAD:** `7878ddf` (deployed)
**Tag:** `v0.9.25-bear-hunter-ui`
**وضعیت:** ✅ Deployed — Endpoint + UI زنده، Runner در حالت manual

---

## 🎯 ۱. ماموریت

اولین ربات live برای حسین که در بازار نزولی short بزنه. سرمایه ۱۰۰k تومان، paper mode اول، بعد live.

**تصمیمات قفل‌شده:**
| پارامتر | مقدار |
|---------|-------|
| سرمایه اولیه | ۱۰۰,۰۰۰ تومان |
| سقف روزانه | ۳۰۰,۰۰۰ تومان |
| سقف هر سفارش | ۱۰۰,۰۰۰ تومان |
| حداکثر پوزیشن | ۴ |
| جفت‌ارز | BTCTMN |
| تایم‌فریم | ۱h |
| SL / TP | ۳٪ / ۴.۵٪ |
| Cooldown | ۶۰ ثانیه |
| اهرم | ۱x |
| حد زیان ۸h | -۵٪ → kill switch |
| TTL سیگنال | ۱۰ روز |

---

## 🏗️ ۲. معماری (تکمیل‌شده)

### Backend
    backend/app/
    ├── domain/ports/
    │   └── margin_exchange.py           ← Port + DryRunError + DryRunReason
    ├── infrastructure/exchange/wallex/
    │   └── margin_adapter.py            ← WallexMarginAdapter (real schema)
    ├── services/bots/bear_hunter/
    │   ├── paths.py                     ← absolute paths (cwd-independent)
    │   ├── config.py                    ← BearHunterConfig (frozen, 16 fields)
    │   ├── state.py                     ← BearHunterState + HumanSignal + StateStore
    │   ├── rules.py                     ← pure math (Decimal, 6 functions)
    │   ├── pre_flight.py                ← 22 checks in 5 phases + synthetic paper
    │   ├── presence.py                  ← PresenceTracker (48/72/96h + rate-limit + timeout)
    │   ├── audit.py                     ← WAL pattern
    │   ├── executor.py                  ← Paper vs Live
    │   └── runner.py                    ← main entrypoint (--once, --verbose, --interval)
    ├── presentation/api/v1/
    │   ├── live_bot.py                  ← 4 endpoints (status, signal, kill, resume)
    │   └── router.py                     ← registered
    └── scripts/
        └── init_bear_hunter_user.py     ← CLI to bootstrap user state

### Frontend
    frontend/
    ├── app/(app)/bear-hunter/page.tsx    ← main page (401 redirect)
    ├── components/bear-hunter/
    │   ├── status-card.tsx               ← 8-state badge
    │   ├── signal-card.tsx               ← 3 direction buttons
    │   └── controls-card.tsx             ← kill + resume
    ├── lib/hooks/use-bear-hunter.ts     ← React Query (5s polling)
    └── components/layout/sidebar.tsx     ← sidebar link added

### Scripts (debug/monitor)
    backend/scripts/
    ├── debug_wallex_raw.py               ← raw JSON debug
    ├── test_margin_liquidity.py          ← 10 markets × 3 sizes
    ├── test_margin_view_token.py         ← initial auth test
    └── liquidity_monitor.py              ← hourly poller

---

## 📊 ۳. آمار

| متریک | مقدار |
|-------|-------|
| فایل Python جدید | ~۱۵ |
| خطوط کد | ~۳,۵۰۰ |
| تست‌های unit | **۸۰** (همه پاس) |
| Endpoint جدید | ۴ |
| صفحه جدید | ۱ |
| کامپوننت جدید | ۳ |
| Commitها | ۸ |
| زمان اجرای تست | ۰.۴ ثانیه |

### توزیع تست‌ها
| فایل | تعداد |
|------|-------|
| test_rules.py | ۱۵ |
| test_state_reconcile.py | ۸ |
| test_executor.py | ۳ |
| test_runner.py | ۳ |
| test_human_signal.py | ۱۲ |
| test_presence.py | ۱۹ |
| test_waiting_liquidity.py | ۲۰ |
| **جمع** | **۸۰** |

---

## 🐛 ۴. باگ‌های کشف و رفع‌شده (۱۴)

| # | باگ | کشف |
|---|-----|-----|
| ۱ | float + Decimal در pre_flight | تست unit |
| ۲ | position_size_pct (0.15 → 15.0) | تست unit |
| ۳ | loss_8h_pct → pnl_8h_pct | تست unit |
| ۴ | liquidation_price → liquidity_price | تست runner |
| ۵ | Retry روی POST = پوزیشن تکراری | دی دریا |
| ۶ | .get() مخفی schema mismatch | دی دریا |
| ۷ | Paper mode بدون PaperExecutor | دی دریا |
| ۸ | .com → .ir (URL) | شاهد |
| ۹ | kill_switch_active → is_killed | تست |
| ۱۰ | check_index در ADR | دی دریا |
| ۱۱ | last_presence_alert_at anchor | کرش اسکریپت |
| ۱۲ | bot_status = "killed" → "killed_manual" | تست |
| ۱۳ | مسیر state (backend/backend/) | runtime |
| ۱۴ | Paper mode بدون synthetic dry_run | runtime |

---

## 🚨 ۵. کشف بحرانی: نقدینگی والکس صفر

**تست ۱۰ market × ۳ اندازه = ۳۰ ترکیب:**

| نتیجه | تعداد |
|-------|-------|
| NO_LIQUIDITY | ۲۴ |
| 422 (invalid market) | ۶ |
| OK | **۰** |

**پیام والکس:**
    در حال حاضر، ظرفیت برای پرداخت اعتبار بیت‌کوین به اتمام رسیده است.

**راه‌حل:**
- `WAITING_LIQUIDITY` state (مشتق از `waiting_liquidity_since`)
- Liquidity monitor هر ۱ ساعت
- Paper mode با synthetic dry_run (بدون نیاز به نقدینگی واقعی)

---

## ✅ ۶. محافظ‌های امنیتی (۱۳)

| محافظ | فایل |
|-------|------|
| asyncio.Lock (tick parallel) | runner.py |
| asyncio.timeout(60) | runner.py |
| Kill switch پس از ۳ خطا | runner.py |
| KeyboardInterrupt → save | runner.py |
| Retry فقط GET | margin_adapter.py |
| Hard block paper mode | executor.py |
| _REQUIRED_POSITION_FIELDS | margin_adapter.py |
| API key masking (__repr__) | margin_adapter.py |
| Liquidity cache (5 min) | state.py |
| Rate-limit alert (6h) | presence.py |
| Alert timeout (5s) | presence.py |
| Auth guard frontend (401 → /login) | page.tsx |
| resume force=true برای auto kill | live_bot.py |

---

## 🌐 ۷. Endpoints (deployed)

| Method | Path | Auth | Validation |
|--------|------|------|------------|
| GET | /v1/user/live-bot/status | JWT | — |
| POST | /v1/user/live-bot/signal | JWT | Literal[3] + ttl_days[1-90] + note[200] |
| POST | /v1/user/live-bot/kill | JWT | reason[3-200] |
| POST | /v1/user/live-bot/resume | JWT | reason[3-200] + force (required for auto kill) |

**State:**
- per-user JSON: `backend/data/bots/bear_hunter/users/{user_id}.json`
- audit trail: `{user_id}.audit.jsonl`
- read-through (no cache, per Di Darya review)

---

## 🚀 ۸. Deploy Status

**سرور:** `87.248.152.239:9011` → `/home/deploy/wallex/`

| مورد | وضعیت |
|------|-------|
| Backend rsync | ✅ 47 KB |
| Backend chown | ✅ deploy:deploy |
| Backend restart | ✅ active |
| Frontend rsync | ✅ 13 KB |
| Frontend build | ✅ 28 routes |
| Frontend restart | ✅ active |
| E2E: endpoint 401 | ✅ |
| Tag | ✅ v0.9.25-bear-hunter-ui |

**⚠️ چیزی که deploy شد:**
- ✅ ۴ endpoint جدید
- ✅ صفحه /bear-hunter
- ✅ sidebar link

**⚠️ چیزی که deploy نشد (طبق دستور دی حامی):**
- ❌ systemd runner (پایین رو ببین)
- ❌ LIVE_TRADING_ENABLED=True
- ❌ توکن View روی سرور

---

## 💾 ۹. Commit Log

    7878ddf  feat(ui): add bear-hunter to sidebar             (pushed)
    a247f1b  fix(bear_hunter): absolute paths + init script   (pushed)
    a527da1  fix(bear_hunter): paper mode synthetic dry_run   (pushed)
    2c2c445  feat(api,ui): bear-hunter endpoints + dashboard  (pushed)
    7d36771  feat(bear_hunter): presence tracker phase 1.1
    7126d5b  feat(bear_hunter): phase 0 complete + ADR 0020
    8ab3ba9  docs(adr): 0019 margin trading & bear hunter
    92c1662  docs: MVP roadmap

**Tags:**
- `v0.9.25-pre-bear-hunter-deploy`
- `v0.9.25-bear-hunter-ui` (فعلی)

---

## 📝 ۱۰. ADRs

| # | عنوان | وضعیت |
|---|-------|-------|
| 0019 | Margin Trading & Bear Hunter | ✅ Accepted |
| 0020 | Human-in-the-Loop + Lending Capacity | ✅ Accepted |
| 0021 | Short Strategy (RSI + resistance) | ⏳ آینده |

---

## 🎯 ۱۱. قدم‌های بعدی

### فوری (فردا — بعد از تأیید دی حامی)
1. **Paper mode ۲۴/۷** — runner بدون توکن:
   - `main()` بدون `WALLEX_VIEW_TOKEN` کار کنه
   - `_reconcile()` در paper_mode skip
   - `_generate_mock_signal` از `/v1/markets` (عمومی)
   - اجرا در `tmux` لوکال (بدون systemd)
2. **تست ۷ روز** — آمار paper mode
3. **بعد:** tag `v0.9.26-paper-mode-started`

### کوتاه‌مدت
4. **استراتژی short واقعی** (`_generate_short_signal`):
   - RSI(14) > 70
   - ADX > 25
   - ۳ کندل تایید
5. **ADR 0021** — short strategy
6. **مانیتور نقدینگی** در tmux

### بعد از ۳۰ روز paper
7. **Live mode** — از `User.wallex_token_encrypted` موجود (Fernet)
8. **systemd unit** برای runner (با access به DB)
9. **Trade token** از UI (`/settings/wallex`)

---

## 🔐 ۱۲. یادآوری‌های امنیتی

1. **توکن `21387|...`** — حسین تأیید کرد revoke شد ✅
2. **توکن جدید** — `~/.wallex_view_token` روی لوکال (chmod 600) — **روی سرور نیست** (طبق دستور)
3. **Paper mode** — هیچ توکنی نیاز نداره (فقط market data عمومی)
4. **Live mode (بعد)** — از `User.wallex_token_encrypted` می‌خونیم (نه فایل جدا)
5. **`.env` سرور** — `chmod 600`, owner deploy
6. **`data/bots/`** — در `.gitignore` (state + audit untracked)

---

## 📚 ۱۳. مستندات مرتبط

- `docs/adr/0019-margin-bear-hunter.md`
- `docs/adr/0020-human-in-the-loop.md`
- `HANDOFF-LIVE-BOT-2026-10-18.md` (نامه دی سرپرست)
- `backend/data/bots/bear_hunter/liquidity_log.jsonl` (شاهد نقدینگی)

---

## 🎓 ۱۴. درس‌های کلیدی

1. **ترتیب کار مهم‌تر از سرعت:** UI قبل از Runner = scope creep (نقد دی حامی)
2. **Paper mode بدون نقدینگی:** با synthetic dry_run می‌شه ۳۰ روز تمرین کرد
3. **Paper mode بدون توکن:** فقط market data عمومی + capital از config
4. **Single-writer pattern:** Backend می‌نویسه state، Runner در فاز بعد می‌خونه
5. **Anchor exact:** حتماً قبل از patch، متن دقیق رو با grep ببین (چند AssertionError)
6. **Bash timeout:** heredoc بزرگ ممکنه truncate بشه — با python write_text بهتره

---

## 🌟 ۱۵. خلاصه برای دی حامی

| سؤال | جواب |
|-------|------|
| Paper mode نیاز به توکن؟ | ❌ نه (کشف مهم) |
| Storage امن (live)? | `User.wallex_token_encrypted` موجود |
| Deploy الان؟ | ✅ انجام شد (بدون runner) |
| Fernet جدید؟ | ❌ نه، همون WALLEX_TOKEN_ENC_KEY |
| runner systemd؟ | ⏳ فاز بعد (بعد از paper mode ۷ روز) |

**پایان گزارش — نسخه ۲.۰**
