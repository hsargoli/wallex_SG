# 🧠 سفر ML — خلاصه و درس‌ها

**تاریخ:** ۱ اکتبر ۲۰۲۶  
**وضعیت:** ML فعلاً در انتظار (به‌خاطر کمبود داده)  
**تصمیم:** ادامه با استراتژی قانونی، برگشت به ML بعد از ۶ ماه

---

## 📊 چی ساختیم

### مدل‌های ML

app/services/
├── ml_bottom_model.py # RandomForest برای کف‌شناسی
├── position_sizer.py # Gradient Boosting Regression
├── volatility_predictor.py # پیش‌بینی نوسان
└── anomaly_detector.py # Isolation Forest
text


### اسکریپت‌های آموزش

scripts/ml/
├── bottom_ml.py, v2, v3, v4, v5, v6 # آموزش‌های تدریجی
├── analyze_overfit.py # کشف Overfitting
├── feature_selection.py # انتخاب feature
├── pipeline_lgbm.py # LightGBM
├── retrain_v2.py # آموزش با داده بیشتر
├── test_4h_ml.py # تست 4h
├── test_regime_filter.py # تست regime filter
└── september_replay.py # تست چند مدل
text


---

## 🎓 درس‌های کلیدی

### ۱. Overfitting شدید

In-Sample: AUC = 0.96 ← تقریباً کامل!
Out-of-Sample: AUC = 0.52 ← تصادفی
Gap: -0.44
text


### ۲. Non-Stationarity مشکل اصلی
بازار کریپتو دائماً حال و هواش عوض می‌شه.
مدل روی فاز X آموزش می‌بینه، روی فاز Y تست می‌شه.

### ۳. داده کم = فاجعه ML

داریم: ~2,500 نمونه (20 روز)
نیاز: 50,000+ نمونه (2-3 سال)
text


### ۴. مدل ساده بهتر از پیچیده
| مدل | Test AUC | Gap |
|---|---|---|
| RF | 0.38 | +0.44 |
| LightGBM | 0.46 | +0.51 |
| Logistic | **0.40** | **+0.19** ⭐ |
| SVM | 0.38 | +0.21 |

**Logistic Regression کمترین overfit رو داشت.**

### ۵. ML در ترید ≠ ML در کلاسیک
- سیگنال ضعیفه (AUC 0.55)
- نویز زیاده
- نیاز به ensemble و feature engineering عمیق

### ۶. راه‌حل واقعی: ML به‌عنوان کمک‌کننده، نه تصمیم‌گیرنده

❌ ML تصمیم می‌گیره که بخره یا نه
✅ ML کمک می‌کنه:

    Anomaly Detection (محافظت)

    Volatility Forecast (تنظیم SL/TP)

    Regime Detection (تشخیص فاز)

    Signal Quality (امتیاز به سیگنال)

text


---

## 🚧 مشکلاتی که فیکس کردیم

### باگ Wallex
```python
# قبل:
MAX_BASE_CANDLES = 5000    # محدودیت مصنوعی!
limit <= 1000              # محدودیت اشتباه

# بعد:
MAX_BASE_CANDLES = 30000   # Wallex تا 27K می‌ده
limit <= 3000

# نتیجه: 15m از 367 → 1819 کندل (5 برابر)

SVC deprecation
python

# قبل:
SVC(probability=True)  # deprecated

# بعد:
CalibratedClassifierCV(SVC())  # روش جدید

📈 نتایج نهایی
Backtest استراتژی قانونی (بدون ML)
text

سرمایه:     300,000 → 480,000 تومان
بازده:      +60.39%
Win Rate:   59.6%
ترید:       178

Backtest با Trading Brain
text

سرمایه:     300,000 → 310,030 تومان
بازده:      +3.34%
Win Rate:   54.3%
ترید:       35

نتیجه: استراتژی قانونی خالص بهتره.
🎯 چرا ML فعلاً جواب نمی‌ده؟
دلیل	توضیح
داده کم	فقط 20 روز از Wallex
Non-Stationarity	بازار دائماً تغییر می‌کنه
نویز بالا	کریپتو در 15m پر از نویزه
Featureهای ضعیف	فقط rsi_low_5 ارزش داشت (MI=0.28)
Overfitting	مدل‌های پیچیده داده رو حفظ می‌کنن
🚀 نقشه‌ی ML برای آینده
فاز ۱: Data Collection (۳-۶ ماه)
text

- Background job هر 15 دقیقه
- ذخیره در SQLite/DuckDB
- 5 نماد × 96 کندل/روز = 480 کندل/روز
- بعد 6 ماه: ~90,000 کندل
- نمونه‌ی کافی برای ML ✅

فاز ۲: ML Ensemble (بعد از داده کافی)
text

- Stacking: RF + LGBM + XGB + CatBoost
- Meta-Learner روی خروجی‌ها
- Purged K-Fold Cross-Validation

فاز ۳: Meta-Labeling
text

- ML فقط تشخیص می‌ده که "سیگنال قانونی درسته یا نه"
- این روش با داده کم هم کار می‌کنه
- احتمالاً بهترین رویکرد برای پروژه‌ی ما

فاز ۴: Deep Learning (اختیاری)
text

- LSTM برای سری‌های زمانی
- Transformer-based (TimeGPT)
- نیاز به GPU (که داریم)

💡 درس نهایی
text

ML در ترید با داده کم = شکست
ML با داده کافی = ممکنه کار کنه
ML + استراتژی قانونی = بهترین ترکیب

استراتژی قانونی + ML به‌عنوان کمک‌کننده = راه حرفه‌ای.

نه ML به تنهایی، نه قانون به تنهایی.
📚 منابع برای مطالعه‌ی بعدی

    Advances in Financial Machine Learning — Marcos López de Prado

    Machine Learning for Asset Managers — Marcos López de Prado

    Purged K-Fold Cross-Validation (تکنیک کلیدی)

    Meta-Labeling (روش پیشنهادی برای آینده)

    Triple Barrier Labeling (بهبود Label)

تصمیم نهایی: برگشت به استراتژی قانونی، ذخیره‌ی خودکار داده، ML در ۶ ماه آینده.

نتیجه: پروژه‌ی حرفه‌ای که ML رو در جای درست استفاده می‌کنه، نه جای اشتباه.
