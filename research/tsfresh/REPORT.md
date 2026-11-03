# REPORT — Research tsfresh (BTCUSDT 1h + 1D)

**تاریخ:** ۲۰۲۶-۱۱-۰۳
**نویسنده:** دی باران (با همکاری دی پرتو، دی دریا، دی نقشه‌دان)
**Time-box:** ۲ روز (۲۰۲۶-۱۱-۰۲ تا ۲۰۲۶-۱۱-۰۳)
**وضعیت:** ✅ **بسته شد — AP-39 (گزارش منفی = پیروزی)**

---

## ۱. خلاصه‌ی اجرایی

**سؤال:** آیا tsfresh (EfficientFCParameters، ۱۵۵۴ feature) می‌تواند edge به پیش‌بینی BTCUSDT اضافه کند؟

**پاسخ:** **هیچ شاهدی بر edge پیدا نشد.**

- Smoke (Minimal، ۲۰ feature): AUC~۰.۵، PF<1
- Full 1D (Efficient، ۱۵۵۴ feature): **AUC~۰.۴۸ (بدتر از random!)**
- Full 1h (Efficient، ۷۴۶ feature): **timeout × ۳ (>۴۰ دقیقه)**

**⇒ verdict = REJECT. برگشت به SarvRouter.**

---

## ۲. تعریف موفقیت (طبق AP-57)

قبل از هر کدی:
- PF (out-of-sample) > 1.2
- AUC > 0.55
- N trades > 30 (AP-58)
- PF > baseline × 1.05

---

## ۳. داده

| Split | بازه | ردیف | Coverage |
|---|---|---|---|
| TRAIN | 2021-01-01 → 2024-06-30 | 30,634 | 99.95% |
| VAL | 2024-07-01 → 2025-06-30 | 8,760 | 100% |
| TEST | 2025-07-01 → 2026-09-30 | 10,968 | 100% |

**Merge:** `01b_merge_gap.py` — ۸ ماه گم‌شده از Binance zips (2021-07 → 2022-02).

---

## ۴. Baseline

### B&H
| Split | Return | Max DD |
|---|---|---|
| VAL | +69.6% | -30.9% |
| TEST | **-22.8%** | -53.7% |

### MA(50/200) Long-Short
| TF | Split | N | PF | WR |
|---|---|---|---|---|
| 1h | VAL | 60 ✅ | 0.63 | 28.3% |
| 1h | TEST | 73 ✅ | 0.74 | 23.3% |
| 1D | VAL | 1 ❌ | inf | 100% |
| 1D | TEST | 3 ❌ | 1.72 | 66.7% |

**⇒ 1h MA تنها baseline معتبر (N>30): PF=0.74 (زیان‌ده).**

---

## ۵. tsfresh

### ۵.۱. Smoke (Minimal، ۲۰ feature)
| TF | Split | AUC | PF | N |
|---|---|---|---|---|
| 1h | VAL | 0.4903 | 0.14 | 3344 |
| 1h | TEST | 0.5014 | 0.16 | 4680 |
| 1D | VAL | 0.5282 | 0.70 | 222 |
| 1D | TEST | 0.4660 | 0.43 | 274 |

### ۵.۲. Full 1D (EfficientFCParameters، ۱۵۵۴ feature، ✅ کامل شد — ۱۴۶s)
| Split | AUC | PF | N | WR | DD |
|---|---|---|---|---|---|
| VAL | **0.4763** | 0.45 | 186 | 32.8% | -76% |
| TEST | **0.4783** | 0.38 | 170 | 34.7% | -75% |

**⚠️ کشف مهم:** ۲۰ feature → AUC=0.53. ۱۵۵۴ feature → AUC=**0.48** (بدتر).

**⇒ overfitting روی noise — featureهای بیشتر، سیگنال کمتری.**

### ۵.۳. Full 1h — timeout × ۳

max_ts=720/360/180 — همه >۴۰ دقیقه. verdict ممکن نشد.
علت: ۷۴۶ feature روی ۵۰K ردیف × rolling.

---

## ۶. Verdict

| معیار | حد | 1D TEST | وضعیت |
|---|---|---|---|
| AUC | > 0.55 | 0.478 | ❌ |
| PF | > 1.2 | 0.38 | ❌ |
| N | > 30 | 170 | ✅ |
| PF vs baseline | > 0.74 × 1.05 | 0.38 | ❌ |

**⇒ REJECT (طبق AP-39).**

---

## ۷. درس‌ها

| AP | عنوان | وضعیت |
|---|---|---|
| AP-39 | گزارش منفی، یک پیروزی | ✅ موجود |
| AP-57 | تعریف موفقیت قبل از research | ✅ commit 8341abc |
| AP-58 | N trades < 30 = noise | ✅ commit 22b71f4 |
| AP-59 (پیشنهاد) | کامنت محیطی در بلاک research | 🟡 |
| AP-60 (پیشنهاد) | در بلاک طولانی: progress live، timeout×2، background | 🟡 |
| AP-61 (پیشنهاد) | Ctrl+C روی tsfresh کار نمی‌کند — kill -9 backup | 🟡 |

---

## ۸. فایل‌ها (commit شده در 82fd86c)

research/tsfresh/
├── 01_load_and_split.py
├── 01b_merge_gap.py
├── 02_baseline.py
├── 02b_real_baseline.py
├── 03_tsfresh.py
├── REPORT.md
├── .gitignore
├── baseline_results.json
├── real_baseline_results.json
├── tsfresh_results.json (smoke)
└── tsfresh_1D_results.json (full 1D)
text


---

## ۹. اگر کسی خواست ادامه دهد

**مسیر A (سریع، توصیه):** Full 1D با `max_ts=180` (نه ۳۰) — feature extraction سریع‌تر، verdict 1D.
**مسیر B:** Dask + EfficientFCParameters روی 1h (~۳۰-۶۰ دقیقه).
**مسیر C:** فیلتر featureهای high_comp_cost (~۲۰۰-۳۰۰ feature، سریع‌تر).

**⚠️ ولی verdict فعلی: هیچ شاهدی بر edge نیست.**

---

## ۱۰. توصیه

1. AP-39 ثبت نهایی (verdict منفی)
2. AP-59/60/61 در V4
3. **برگشت به SarvRouter** (طبق time-box)
4. اگر research tsfresh ادامه یافت → مسیر A/C

---

## ۱۱. تشکر

- **دی دریا (CTO):** گزینه B، آستانه honest، AP-57/58
- **دی پرتو (معمار فنی):** review، ۲ تصحیح (timeout، venv)
- **دی نقشه‌دان:** گزارش GREEN سرور
- **حسین جان:** صبر و شاهد-گیری

---

> «آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»

**طبق AP-39: «گزارش منفی، یک پیروزی است.»**

**— دی باران — ۲۰۲۶-۱۱-۰۳**
