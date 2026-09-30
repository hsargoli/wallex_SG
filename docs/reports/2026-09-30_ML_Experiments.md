# 🧪 گزارش آزمایش‌های ML — ۳۰ سپتامبر ۲۰۲۶

**هدف:** بررسی امکان استفاده از Machine Learning برای پیش‌بینی جهت قیمت

**نتیجه‌ی کلی:** ❌ ML فعلاً کار نمی‌کند — داده کافی نیست

---

## 📋 خلاصه‌ی تصمیم

**تصمیم گرفته شد ML به تعویق بیفتد** و به‌جایش رویکرد **Rule-Based** (قوانین دستی) و **Journal** پیاده‌سازی شود.

**دلیل:** با ~۱۲۵-۷۰۰ نمونه، هیچ مدل ML نمی‌تواند الگوهای قابل اتکا یاد بگیرد.

---

## 🧪 سه آزمایش انجام‌شده

### آزمایش ۱: quick_train.py (v1)

**تنظیمات:**
- نماد: BTCTMN
- تایم‌فریم: 1h
- کندل: ۱۰۰۰ (فقط ۶۹۵ برگشت)
- Feature: ۱۴
- Model: RandomForest (n=100, depth=8)
- Target: direction_4

**نتیجه:**
```
Accuracy:       0.4916  (بدتر از baseline 0.5511)
Improvement:   -5.95%
```

**درس:** با ۶۹۵ کندل، مدل شکست خورد.

---

### آزمایش ۲: quick_train_v2.py (v2)

**تغییرات:**
- Feature: ۲۵ (lag features, volume trend, volatility)
- Target های مختلف: direction_1 تا direction_5, return threshold

**نتیجه:**
```
direction_1   acc=0.4860  baseline=0.5294  improvement=-4.34%
direction_2   acc=0.5421  baseline=0.5402  improvement=+0.18%
direction_3   acc=0.4935  baseline=0.5341  improvement=-4.06%
direction_4   acc=0.4486  baseline=0.5480  improvement=-9.94%
direction_5   acc=0.4879  baseline=0.5697  improvement=-8.18%

return_4 > 0.3%   acc=0.6168  baseline=0.3746  ← فریبنده!
return_4 > 0.5%   acc=0.7234  baseline=0.2786  ← فریبنده!
return_4 > 1.0%   acc=0.8748  baseline=0.1254  ← فریبنده!
```

**درس:** 
- Direction targets شکست خوردند
- Threshold targets به‌خاطر **class imbalance** دقت بالا نشون دادن
- مدل فقط class اکثریت رو انتخاب می‌کرد (یاد نگرفته بود)

---

### آزمایش ۳: quick_train_v3.py (v3)

**تغییرات:**
- تایم‌فریم: 4h (داده بیشتر)
- `class_weight='balanced'` 
- معیارها: Precision, Recall, F1, AUC, Precision@top20

**نتیجه:**
```
direction_1: AUC=0.5578  Precision@top20=0.70  n=125
direction_2: AUC=0.4958  Precision@top20=0.50  n=125
direction_3: AUC=0.5740  Precision@top20=0.75  n=125
direction_4: AUC=0.5427  Precision@top20=0.65  n=125
direction_6: AUC=0.5616  Precision@top20=0.80  n=125
```

**درس:**
- AUC همه بین 0.49-0.57 (تقریباً random)
- فقط ۱۲۵ نمونه → آماری بی‌معنا
- Precision@top20 با n=25 محاسبه شده → خطای بالا

---

## 🔍 تحلیل علل شکست

### ۱. داده‌ی بسیار کم (علت اصلی)
| منبع | تایم‌فریم | کندل | بازه |
|---|---|---|---|
| Wallex | 1h | 695 | ~۳۰ روز |
| Wallex | 4h | 125 | ~۲۰ روز |
| Nobitex | 1h | 500 | ~۲۰ روز |

**حداقل موردنیاز برای ML:** ۵۰۰۰-۱۰,۰۰۰ نمونه

### ۲. محدودیت‌های API
- Wallex: ~۱۰۰۰ کندل max در هر درخواست
- Nobitex: ۵۰۰ کندل max
- بدون دسترسی به داده‌ی تاریخی طولانی

### ۳. عدم تعادل کلاس در بعضی Targetها
- `return > 1%` → فقط ۱۲٪ نمونه مثبت
- Accuracy فریبنده می‌شود

### ۴. Feature های عمومی
- MA, EMA, RSI, Volume
- اینها همه‌جا هستند، مزیت رقابتی ندارند
- نیاز به feature های عمیق‌تر (Order Book, Multi-TF)

---

## ✅ چیزهایی که یاد گرفتیم

### ۱. معیار درست مهم‌تر از دقت است
- **Accuracy** برای data نامتعادل گمراه‌کننده است
- **AUC-ROC** معیار واقعی جداسازی کلاس‌هاست
- **Precision@Top-K** برای تصمیم معاملاتی مفید است

### ۲. `class_weight='balanced'` ضروری است
- بدون آن، مدل فقط class اکثریت را انتخاب می‌کند
- با آن، هر دو کلاس جدی گرفته می‌شوند

### ۳. TimeSeriesSplit برای داده‌ی زمانی
- نباید از `train_test_split` معمولی استفاده کرد
- داده‌ی زمانی باید ترتیبی بماند

### ۴. سقف API جدی است
- اکثر صرافی‌ها ۵۰۰-۱۰۰۰ کندل می‌دهند
- برای ML نیاز به ذخیره‌سازی تاریخی خودمان داریم

---

## 🛠️ زیرساخت ML ساخته‌شده (قابل استفاده در آینده)

### اسکریپت‌ها
```
scripts/ml/
├── quick_train.py      ← نسخه اول (direction_4, 1h)
├── quick_train_v2.py   ← نسخه دوم (multi-target, threshold)
└── quick_train_v3.py   ← نسخه سوم (4h, class_weight, AUC)
```

### کتابخانه‌های نصب‌شده
- scikit-learn 1.9.1
- pandas 3.0.6
- numpy 2.5.3
- scipy 1.18.1
- joblib 1.6.0

### قابلیت‌های آماده
- ✅ دریافت کندل از Wallex (UDF format)
- ✅ ساخت ~۲۵ Feature از کندل‌ها
- ✅ ساخت Label برای direction_N
- ✅ ساخت Label برای return threshold
- ✅ آموزش RandomForest با TimeSeriesSplit
- ✅ محاسبه AUC, Precision, Recall, F1
- ✅ Precision@Top-K

---

## 🚀 برای آینده‌ی دور — راه‌حل‌های ممکن

### 🅰️ جمع‌آوری داده‌ی تاریخی طولانی‌مدت
- **ذخیره‌ی خودکار**: هر ساعت کندل جدید را در DB ذخیره کنیم
- **بعد از ۶ ماه**: ~۴۵۰۰ کندل ۱ ساعته
- **بعد از ۱ سال**: ~۹۰۰۰ کندل ۱ ساعته

**پیاده‌سازی:** Background task + SQLite/PostgreSQL

### 🅱️ جمع‌آوری از منابع متعدد
- Wallex (1h, 4h, 1D)
- Nobitex (1h, 4h, 1D)
- CoinGecko (روزانه)
- **جمع: ~۳۰۰۰-۵۰۰۰ کندل** (بهتر ولی هنوز کم)

### 🅲 Feature های عمیق‌تر
- **Order Book Features**: bid/ask imbalance, spread dynamics
- **Multi-Timeframe**: روند 1D روی 1h
- **Wavelet Transform**
- **Candlestick Patterns** (کشف خودکار)

### 🅳 مدل‌های پیشرفته‌تر
- **XGBoost / LightGBM**
- **LSTM / GRU** (برای داده‌ی ترتیبی)
- **Transformer-based** (مثل TimeGPT)
- **Ensemble Methods**

### 🅴 داده‌ی خودمان
- از Journal معاملات واقعی، داده‌ی برچسب‌دار بسازیم
- **بالاترین کیفیت** چون خودت برچسب می‌زنی

---

## 🎯 نتیجه‌ی نهایی

**ML برای الان کنار گذاشته شد.**  
**رویکرد جدید:** Rule-Based + Journal  
**بازگشت به ML:** وقتی داده‌ی کافی جمع شد (~۵۰۰۰+ نمونه)

---

## 📚 منابع برای مطالعه

### مقالات
- "Advances in Financial Machine Learning" — Marcos López de Prado
- "Machine Learning for Asset Managers" — Marcos López de Prado
- "Deep Learning for Time Series Forecasting" — Jason Brownlee

### معیارهای مهم
- AUC-ROC, Precision@K, Sharpe Ratio
- Purged K-Fold Cross-Validation
- Feature Importance (SHAP)

### ابزارها
- `scikit-learn`, `xgboost`, `lightgbm`
- `pandas-ta`, `TA-Lib`
- `shap`, `yellowbrick`

---

**تاریخ گزارش:** ۲۰۲۶-۰۹-۳۰  
**وضعیت:** ML به تعویق افتاد — Rule-Based شروع می‌شود  
**بازنگری بعدی:** وقتی ۵۰۰۰+ نمونه جمع شد
