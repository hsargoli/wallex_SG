# Research — سروپایا

> این پوشه، researchهای exploratory تیم سروپایا را نگه می‌دارد.
> هدف: کشف edge، validate ایده، یا ساخت insight — **قبل از** ورود به production.

## ساختار

research/
├── README.md (این فایل)
└── tsfresh/ # Research tsfresh (2026-11-02/03)
├── 01_load_and_split.py
├── 01b_merge_gap.py
├── 00c_merge_all_symbols.py
├── 02_baseline.py
├── 02b_real_baseline.py
├── 03_tsfresh.py
├── 04_similarity.py
├── REPORT.md
└── data/
text


## قوانین Research (طبق AP-57)

### ۱. تعریف موفقیت قبل از کد
هر research باید **قبل از نوشتن کد**، تعریف کند:
- «موفقیت چیست؟» (PF>1.2؟ AUC>0.55؟)
- «baseline واقعی چیست؟» (B&H، MA Crossover، Long-Short)
- «اگر fail شد، چه نتیجه‌ای بگیریم؟» (AP-39: گزارش منفی = پیروزی)

### ۲. خط سرخ
- ❌ هیچ کد research به `backend/app/` نمی‌رود.
- ❌ هیچ تغییر در SarvRouter/nooaah.
- ✅ فقط `research/` + `frontend/public/data/` (JSON static).

### ۳. Time-box
هر research زمان‌بندی مشخص دارد. اگر در time-box verdict نشد، **توقف و گزارش** (نه تمدید بی‌دلیل).

### ۴. ثبت نتایج
- `REPORT.md` در پوشه‌ی research.
- اگر تصمیم طراحی بود: ADR جدید.
- APهای جدید در `docs/AI_PRIMER_V4.md`.

## Researchهای انجام‌شده

| Research | تاریخ | Verdict | گزارش |
|---|---|---|---|
| tsfresh (BTCUSDT 1h/1D) | 2026-11-02/03 | ❌ no edge (trading) + ✅ insight | `tsfresh/REPORT.md` |
| Similarity page (BTC/ETH/SOL) | 2026-11-03 | ✅ Insight tool (ADR-0033) | `tsfresh/REPORT.md` Part 4 |

## Researchهای آینده (در NEXT_FEATURES.md)
- See `docs/NEXT_FEATURES.md` — بخش tsfresh similarity.

## منابع
- `docs/AI_PRIMER_V4.md` — قوانین طلایی
- `docs/adr/` — تصمیمات معماری
- `docs/NEXT_FEATURES.md` — ایده‌های آینده
