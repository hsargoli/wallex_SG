# گزارش توسعه — ۲۰۲۶-۱۰-۱۰
# WebSocket MVP + Nooaah Phase 1

> یک روز طولانی: بستن WebSocket، و تولد ربات Nooaah (فاز تحلیل)
> نویسنده: حسین + دی (DeepSeek)
> محل: `~/wallex/backend` + `~/wallex/frontend`

---

## خلاصه‌ی یک‌خطی

WebSocket MVP به production رسید (tag + backup)، و ربات Nooaah در قالب DDD subdomain با ۴ لایه متولد شد — از ADR تا صفحه‌ی فرانت `/analysis` با ۳۷۳ نماد.

---

## فاز ۰ — WebSocket MVP (بسته شد)

**قبلاً:** polling در فرانت با ۳s-120s intervals، N×M مسئله.

**امروز:**

- `WallexTickerClient` — sync thread + `websocket-client` (نه python-socketio)
- `TickerFanout` — bridge thread↔asyncio با `call_soon_threadsafe`
- `/ws/ticker/{symbol}` — FastAPI WebSocket endpoint
- `useLiveTicker` hook + `LiveTickerCard` با stale indicator
- ۲۸ تست جدید (۱۳ + ۱۵)
- ADR-0007 (Accepted + Observation + Future Work)
- tag `v0.9.1-realtime-mvp`

**کشف مهم:** Wallex **Socket.IO**ـه، نه WS خالص.
`python-socketio` ۳ بار شکست خورد (اسلش اضافه در path). `websocket-client` یه بار کار کرد.

---

## فاز ۱ — کشف زیرساخت قبلی Nooaah

قبل از نوشتن هر خط کد، grep زدیم:

- `services/regime_detector.py` — rule-based (ADX + ATR% + EMA + ret_20)، کالیبره برای 1h crypto
- `domain/analysis/` — اسکلت خالی (۵ پوشه با `__init__.py` خالی)
- `scripts/archive/ml_experiments/per_asset_analysis.py` — تحلیل مقایسه‌ای هر نماد
- `domain/analysis/models/__init__.py` می‌گفت: `"Pure computation models: feature_math (RSI, volatility, trend, volume-z)."`

**نتیجه:** یه AI قبلی نیت DDD داشته ولی ناتموم مونده. ما **ادامه دادیم، نه از صفر**.

---

## فاز ۲ — ADR-0008 (Accepted)

**ADR-0008 موجود بود (Proposed).** یه Update اضافه کردیم:

- کشف `regime_detector.py` → دور نریزیم
- Phase 1 هر دو classifier رو داره (rule_based + kmeans)
- selector از env: `ANALYSIS_CLASSIFIER=rule_based|kmeans`
- Status: `Proposed → Accepted`
- README sync: 0008 اضافه شد

---

## فاز ۳ — DDD Subdomain (۱۷ فایل جدید)

**معماری ۴ لایه:**

    backend/app/
    ├── domain/analysis/         ← pure، بدون sklearn/numpy
    │   ├── entities/            ← Regime, PersonalityStats
    │   ├── value_objects/       ← FeatureVector, ClusterLabel
    │   ├── ports/               ← FeatureExtractorPort, RegimeClassifierPort
    │   └── models/              ← feature_math (rsi, volatility, trend, adx, atr, ema)
    ├── application/use_cases/
    │   └── analyze_symbol.py    ← AnalyzeSymbolUseCase
    ├── infrastructure/analysis/
    │   ├── ta_features.py       ← implements FeatureExtractorPort
    │   ├── rule_based_classifier.py  ← منتقل از services/regime_detector
    │   ├── kmeans_classifier.py ← sklearn، K با silhouette، percentile labels
    │   └── factory.py           ← build_classifier() از env
    └── presentation/api/v1/
        └── analysis.py          ← GET /v1/analysis/{symbol}?timeframe=1h

**دو باگ کشف و fix شد:**

۱. **context=200 کندل به classifier** (نه ۲۴) — چون `ema_last(100)` حداقل ۱۰۰ کندل می‌خواد. با ۲۴، همیشه `alignment=mixed` → trending هرگز تشخیص نمی‌شد.

۲. **آستانه‌های percentile** (نه ثابت) — چون volatility BTC ~۰.۴۸ـه، آستانه‌ی `vol < 0.5` تقریباً همه رو `ranging` می‌کرد.

---

## فاز ۴ — تست (۲۶ جدید، ۱۵۴ کل)

- `test_feature_math.py` — ۱۱ تست (rsi, volatility, trend, volume_z, adx, atr, ema)
- `test_classifiers.py` — ۱۰ تست (rule_based + kmeans، با داده‌ی مصنوعی)
- `test_analyze_symbol.py` — ۵ تست (mock exchange)

**نتیجه:** rule_based و kmeans **هر دو موافقن** روی BTC:
- dominant `ranging` (۵۳.۹٪)
- trending_up (۲۲.۹٪) > trending_down (۳.۶٪)

---

## فاز ۵ — Data Hygiene

**کشف:** ۱ کندل گم در هر ۳ CSV (BTC/ETH/USDT) در ts=1790082000.

**تلاش اول (Wallex fetch):** شکست خورد — Wallex اون ساعت رو نداشت.

**راه‌حل:** forward-fill با `volume=0` (علامت «معامله‌ای نبود»).

**نتیجه:** همه‌ی فایل‌ها gap-free، ۷۴۷ row.

اسکریپت: `scripts/fix_candle_gap.py`

---

## فاز ۶ — فرانت `/analysis`

**صفحه‌ی تحلیل با:**

- dropdown از `/v1/markets` (۳۷۳ نماد، مرتب بر اساس `daily_quote_volume` نزولی)
- نوار توزیع regime (چهار رنگ)
- ۴ کارت regime (صعودی/نزولی/رنج/پرنوسان — تعداد + درصد)
- ۴ کارت آماری (رژیم غالب، نوسان، RSI، قدرت روند)

**تأیید بصری:**
- **BTCTMN:** رنج غالب (۵۳.۹٪)، نوسان ۰.۴۸٪ → بازار بالغ
- **PUMPTMN:** پرنوسان غالب (۴۵.۱٪)، نوسان ۱.۵۷٪ → altcoin احساسی

**یعنی:** «شخصیت هر ارز» واقعاً کار می‌کنه.

---

## فاز ۷ — GitHub Backup

- private repo: `hsargoli/wallex_SG`
- SSH key (ed25519) setup شد
- ۹ commit + ۲ tag push شد
- پترن push سه‌نقطه‌ای: شب + قبل از کار بزرگ + بعد از tag

---

## فاز ۸ — AI_PRIMER v2.2

**چهار درس امروز:**

- **M17:** فرضیه در ADR ممنوع — فقط داده
- **M18:** یه نمونه ≠ نتیجه — تکرار کن
- **قانون ۱۳:** قبل از ماجراجویی، نقطه‌ی برگشت بساز
- **قانون ۱۴:** library اگه ۲ بار شکست، ابزار عوض کن

---

## Commitهای امروز (۱۱ عدد)

    f414339  docs(adr): add 0007 to README table
    85078bc  docs(adr): 0007 finalize architecture after ws exploration
    e391acc  chore(scripts): add Wallex WS explorer tool
    9a2189d  chore(deps): add websocket-client for Wallex WS client
    505e96e  chore(deps): add aiohttp for python-socketio async handshake
    bb71638  chore(deps): add python-socketio for Wallex Socket.IO client
    1ad3b9f  docs(adr): 0007 websocket realtime decision (proposed)
    4843cde  chore(deps): remove unused python-socketio + aiohttp
    1b9db8d  docs(adr): 0007 finalize with risks and future work
    74059a1  feat(realtime): wallex ticker ws client (backend)
    a60668b  feat(realtime): /ws/ticker/{symbol} endpoint + fanout
    751adea  feat(realtime): useLiveTicker hook + live card (frontend)
    024bfd6  docs(adr): 0007 add MVP verification observation
    9a82543  docs(adr): 0008 — port-based classifier, accepted
    c86e8b8  feat(domain): analysis subdomain
    529cb9d  feat(infra): analysis adapters
    9c62a91  feat(analysis): analyze_symbol use case + /v1/analysis/{symbol}
    2e90e75  feat(frontend): analysis page — dropdown by volume

---

## درس‌های امروز

۱. **جنگ با library ممنوع.** python-socketio → ۳ شکست. websocket-client → ۱ موفقیت.

۲. **تست فیل = هدیه.** `test_start_creates_thread` باگ `timeout=10` رو کشف کرد.

۳. **شاهد قبل از فرضیه.** throttle رو تو ADR ثبت نکردیم (۲ تست، ۲ نتیجه — inconclusive).

۴. **dependency چک کن قبل از الگوریتم نویسی.** ۲۰۰ خط pure KMeans نوشتم، بعد فهمیدم sklearn هست. ۲۰۰ خط دور ریخته شد → قانون ۱۴.

۵. **نقطه‌ی برگشت = جسارت.** tag `v0.9-pre-websocket` اجازه داد بدون استرس ۳ بار python-socketio رو امتحان کنیم.

۶. **AI قبلی = همکار گذشته.** `regime_detector.py` رو دور نریختیم، منتقلش کردیم به DDD.

---

## باقی‌مونده (Phase 2)

- **ربات Nooaah** (`services/bots/nooaah/`) — مصرف‌کننده‌ی analysis engine
- **A/B comparison** — rule_based vs kmeans روی چند نماد
- **آمار پیشرفته** — state transitions (چند بار از رنج به trending رفتیم)
- **WebSocket برای Nooaah** — regime change live
- **`per_asset_analysis` → use case** — DDD شدن

---

## Refs

- ADR-0007 — WebSocket realtime
- ADR-0008 — Nooaah Analysis DDD
- AI_PRIMER v2.2
- branch: `refactor/full-ddd`
- remote: `git@github.com:hsargoli/wallex_SG.git`
