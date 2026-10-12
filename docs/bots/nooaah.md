# 🌿 نوح — Nooaah Bot

**slug:** `nooaah`
**version:** `0.2.0`
**وضعیت:** 🟢 Live (Stage 1 — capital 100K)
**تاریخ ایجاد:** ۲۰۲۶-۱۰-۱۰
**آخرین آپدیت:** ۲۰۲۶-۱۰-۱۲

---

## 📖 استراتژی

ربات **تحلیل‌محور** که «شخصیت» هر ارز را می‌شناسد و بر اساس رژیم بازار تصمیم می‌گیرد.

**فلسفه:** بازار همیشه trending_up نیست. ربات به‌جای تلاش برای پیش‌بینی، **منتظر** می‌ماند تا شرایط ایده‌آل شود. در رنج و نزول، **کاری نمی‌کند** — defensive.

**هدف:** 
- در روند صعودی: سود بگیر
- در روند نزولی: پول را حفظ کن (بدون معامله)
- در رنج: منتظر بمان

---

## 🏗️ معماری

ربات به‌عنوان **DDD Subdomain** ساخته شده (ADR-0008):

    backend/app/
    ├── domain/analysis/         ← منطق خالص (Regime, FeatureVector)
    ├── infrastructure/analysis/  ← rule_based + kmeans + lgbm classifiers
    ├── application/use_cases/   ← analyze_symbol
    ├── services/bots/nooaah/    ← خود ربات (orchestration)
    │   ├── config.py            ← پارامترها
    │   ├── strategy.py          ← propose_trade (pure)
    │   ├── bot.py               ← fetch candles + decide
    │   ├── backtest.py          ← historical simulation
    │   ├── state.py             ← state machine + persistence
    │   ├── executor.py          ← PaperExecutor / LiveExecutor
    │   ├── runner.py            ← orchestrator (bot + executor + state)
    │   └── scheduler.py         ← APScheduler, 30min
    └── presentation/api/v1/     ← /v1/nooaah/*
        └── nooaah.py

قاعده‌ی وابستگی: `presentation → application → domain ← infrastructure`

---

## 🎯 Classifier

پیش‌فرض: **rule_based** (ADR-0008).

معیارها:
- **ADX** ≥ ۲۵ (قدرت روند)
- **بازده ۲۰ کندل** ≥ ۱٪
- **EMA alignment**: EMA(20) > EMA(50) > EMA(100)
- **ATR%** برای محاسبه‌ی TP/SL

**Regimeهای ۴ گانه:**
- `trending_up` ← هدف ورود
- `trending_down`
- `ranging`
- `choppy`

---

## ⚙️ پارامترهای بهینه (از ۱۸ ایده)

| پارامتر | مقدار | توضیح |
|---|---|---|
| `min_confidence` | **۸۵** | حداقل اطمینان (defensive) |
| `confirmation_candles` | ۲ | ۲ کندل متوالی trending_up |
| `tp_atr_mult` | ۳.۰ | TP = entry + 3×ATR |
| `sl_atr_mult` | ۱.۵ | SL = entry − 1.5×ATR |
| `volume_z_min` | **-۰.۵** | فیلتر حجم (A2 — تنها ایده‌ی برنده) |
| `max_concurrent_positions` | ۱ | تک‌پوزیشن |
| `top_n` | ۵ | ۵ نماد پرحجم Wallex |
| `max_duration_hours` | ۲۴ | timeout |
| `daily_loss_limit_pct` | ۳.۶ | سقف ضرر روزانه (قابل تغییر) |

**رژیم فیلتر، momentum exit، trailing: همه خاموش** (tested, rejected)

---

## 🚦 منطق ورود

    ۱. از ۳۷۳ نماد Wallex، ۵ تا پرحجم انتخاب کن
    ۲. برای هر نماد:
       - حجم آخرین کندل ≥ -0.5σ (فیلتر volume)
       - ADX، ret_20، EMA → trending_up?
       - conf ≥ 85?
       - ۲ کندل متوالی trending_up؟ (confirmation)
    ۳. اگه همه شرط‌ها OK → قوی‌ترین proposal

**قوی‌ترین:** بالاترین confidence.

---

## 🛑 منطق خروج

سه راه خروج خودکار + یک راه دستی:

| دلیل | شرط |
|---|---|
| `take_profit` | close ≥ entry + 3×ATR |
| `stop_loss` | close ≤ entry − 1.5×ATR |
| `timeout` | ۲۴ کندل گذشت |
| `manual_sell` | کاربر از UI |

---

## 🔄 State Machine

    paper-testing  →  ready-for-live  →  live-active  ↔  live-paused
                                              ↓
                                           killed
                                          (غیرقابل برگشت)

| حالت | توضیح |
|---|---|
| `paper-testing` | معاملات شبیه‌سازی‌شده (بدون پول واقعی) |
| `ready-for-live` | ۶ شرط paper برآورده، آماده‌ی فعال‌سازی |
| `live-active` | ربات با پول واقعی معامله می‌کند |
| `live-paused` | موقتاً متوقف — قابل resume |
| `killed` | کامل متوقف — نیاز به reset |

---

## 🎬 فعال‌سازی Live — ۶ مرحله (ADR-0012)

**شرایط عبور از paper به ready (ADR-0011):**
- ≥ ۷ روز در paper
- ≥ ۱۰ trade
- Win rate ≥ ۴۰٪
- بازده ۷ روز > ۰
- ۰ kill-switch در ۷ روز
- ۰ daily-loss-hit در ۷ روز

**Wizard 6-step:**
1. Review — paper performance + هشدارها
2. Strategy — min_confidence, cc, tp, sl, vol_z
3. Position — max_positions, top_n
4. Capital — مقدار از wallet
5. Risk — daily_loss_limit
6. Confirm — تایپ «با مسئولیت خودم»

**Staged Rollout:**
| Stage | شرط عبور | سقف سرمایه |
|---|---|---|
| 1 | ۵ برد live | ۱۰٪ wallet |
| 2 | ۱۰ برد + Sharpe ≥ ۰.۳ | ۳۰٪ |
| 3 (full) | ۲۰ برد | ۱۰۰٪ |

---

## 🛑 توقف — ۳ گزینه (ADR-0013)

کاربر با زدن دکمه‌ی «توقف ربات» انتخاب می‌کند:

| گزینه | پوزیشن‌ها | حالت بعدی | قابل resume؟ |
|---|---|---|---|
| **SELL** | همه با `best_bid` فروخته می‌شن، پول برمی‌گرده | `live-paused` | ✅ |
| **PAUSE** | باز می‌مونن | `live-paused` | ✅ |
| **KILL** | باز می‌مونن | `killed` | ❌ (reset) |

**Preview endpoint:** قبل از تصمیم، `GET /live/stop/preview` وضعیت فعلی + PnL را می‌دهد.

---

## ⏱ Scheduler

- **هر ۳۰ دقیقه** — APScheduler درون FastAPI
- هر cycle: reset روزانه → چک kill/cooldown → مدیریت پوزیشن‌ها → proposal جدید → ذخیره state
- Single-worker only (ADR-0010)

### Cooldown بعد از Daily Loss

اگه ضرر امروز به سقف رسید → **۶ ساعت cooldown** (نه تا آخر روز).
بعد از ۶ ساعت → خودکار active می‌شود.

---

## 📊 گزارش چرخه‌ها (Cycle Log)

هر cycle ثبت می‌شود در `state.cycle_logs` (آخرین ۱۰۰):

    {
      "timestamp": ...,
      "status": "ok",
      "action": "no_signal | opened | cooldown | killed | ...",
      "reason_fa": "۵ نماد چک شد — هیچ سیگنال trending_up نبود",
      "opened_symbol": null,
      "opened_confidence": null
    }

**UI:** کارت «گزارش چرخه‌ها» در `/nooaah` — timeline با آیکون و reason.

---

## 📈 نتایج بک‌تست

**بازه‌ی صعودی (Sep 25 → Oct 5):**
| معیار | مقدار |
|---|---|
| بازده | +۲۷.۶۵٪ |
| Sharpe | ۰.۶۳۳ |
| Win Rate | ۸۰.۰٪ |
| max DD | ۳.۵۱٪ |
| tradeها | ۱۵ |

**بازه‌ی نزولی (Oct 5 → Oct 11):**
| معیار | مقدار |
|---|---|
| بازده | ۰٪ (بدون trade) |
| — | defensive ✅ |

**بازه‌ی رنج (Sep 20 → Sep 25):**
| معیار | مقدار |
|---|---|
| بازده | -۴.۱۹٪ (ضعف شناخته‌شده) |

---

## 📚 ۱۸ ایده‌ی تست‌شده

مستند کامل: `docs/nooaah_ideas.md`

| نتیجه | ایده‌ها |
|---|---|
| ✅ **پذیرفته** | A2 (volume filter) |
| 🟡 مرزی | B1 (confidence sizing — leverage) |
| ❌ رد | momentum (۴ حالت), regime filter, trailing ATR, ML (LightGBM v1/v2), RSI filter, multi-TF, max positions, cooldown, daily loss, dynamic ATR, partial exit, stale exit |

**الگو:** استراتژی بسیار حساس است. فقط A2 تونست بهبود بده.

---

## 🚀 API Endpoints

**Status & Config:**
- `GET /v1/nooaah/status` — تحلیل زنده
- `GET /v1/nooaah/config` — state فعلی
- `POST /v1/nooaah/config` — تغییر capital/daily_limit

**Backtest:**
- `GET /v1/nooaah/backtest` — backtest با تاریخ + symbols + params

**Readiness & Activation:**
- `GET /v1/nooaah/readiness` — ۶ شرط
- `GET/PUT/DELETE /v1/nooaah/live/draft` — wizard draft
- `POST /v1/nooaah/live/activate` — فعال‌سازی
- `POST /v1/nooaah/live/stage/advance` — ارتقای stage

**Stop:**
- `GET /v1/nooaah/live/stop/preview`
- `POST /v1/nooaah/live/stop` — {action: sell|pause|kill}
- `POST /v1/nooaah/kill` — سریع
- `POST /v1/nooaah/resume`

**Monitoring:**
- `GET /v1/nooaah/cycles?limit=30` — تاریخچه

---

## 🎨 UI Guide — `/nooaah`

**کارت‌ها به ترتیب:**

1. **آماده برای Live** (اگه paper-testing + conditions سبزن)
2. **پیکربندی و کنترل** — badge status، capital، daily limit، scheduler، دکمه‌ی توقف
3. **گزارش چرخه‌ها** — timeline
4. **تنظیمات اجرا** — date range + preset (احتیاط/عادی/تهاجمی)
5. **وضعیت زنده** — تحلیل الان
6. **نتایج بک‌تست** (collapsible)

**صفحه‌ی `/nooaah/live/activate`:** wizard ۶ مرحله‌ای

---

## 📋 ADRهای مرتبط

| ADR | موضوع |
|---|---|
| 0007 | WebSocket realtime (تحلیل زنده) |
| 0008 | Nooaah Analysis DDD Subdomain |
| 0009 | ML Stack (LightGBM — Accepted، فعلاً غیرفعال) |
| 0010 | Live Trading Architecture |
| 0011 | Live Activation Process |
| 0012 | Multi-Step Live Activation |
| 0013 | Live Stop Actions |

---

## ⚠️ محدودیت‌های شناخته‌شده

- **رنج:** -۴.۱۹٪ در backtest. ربات در رنج ضرر می‌دهد.
- **بازار نزولی:** صفر trade (defensive — این ویژگی است، نه باگ).
- **داده:** Wallex فقط ۲۹ روز hourly می‌دهد.
- **Classifier:** rule_based false positive در رنج دارد.
- **Single-worker:** scheduler با `--workers > 1` مشکل دارد.
- **min_quantity Wallex:** برای BTCTMN با ۱۰۰K زیر حداقل — ممکنه fail بده.

---

## 🚧 Future Work

- Telegram alerts برای trade/cooldown/kill
- `services/bots/nooaah/` رسمی در registry
- KMeans classifier برای A/B comparison
- Per-symbol tuning (PUMPTMN ≠ USDTTMN)
- Redis pub/sub برای multi-worker
- Tooltip برای wizard + modal (UX polish)
- Fix متن cooldown: «فردا» → «۶ ساعت»

---

## 🔗 مراجع

- `docs/nooaah_ideas.md` — ۱۸ ایده‌ی تست‌شده
- `docs/adr/0008-nooaah-analysis-ddd.md`
- `docs/adr/0010-live-trading-architecture.md`
- `docs/adr/0011-live-activation-process.md`
- `docs/adr/0012-multistep-live-activation.md`
- `docs/adr/0013-live-stop-actions.md`
- `docs/reports/2026-10-11_Nooaah_UI.md`
- `backend/scripts/seed_nooaah_paper.py` — dev seed

---

**آخرین آپدیت:** ۲۰۲۶-۱۰-۱۲
**نسخه:** 0.2.0
