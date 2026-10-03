# گزارش رفع باگ stop_Price در API والکس

**تاریخ (میلادی):** 2026-10-04
**تاریخ (شمسی):** 1405/07/12
**وضعیت:** کامل و تست‌شده

---

## مشکل

هنگام ثبت STOP_LIMIT از UI، خطای `400 Bad Request` یا `422` دریافت می‌شد.

## مسیر کشف

### مرحله ۱: فرضیات اولیه (همه اشتباه)

| فرضیه | تست | نتیجه |
|---|---|---|
| client_id مشکل داره | چند فرمت مختلف | ❌ |
| اعداد باید precision کامل داشته باشن | 18 رقم اعشار | ❌ |
| ترتیب price/stopPrice مهمه | ۵ ترکیب مختلف | ❌ |
| شرط `<=`/`>=` مهمه | هر دو | ❌ |

### مرحله ۲: درخواست خام با httpx

| فیلد | نتیجه |
|---|---|
| `stopPrice` + `stopPriceCondition` | **422**: "فیلد قیمت توقف الزامی است" |
| `stop_Price` + `stop_PriceCondition` | **201 Created** ✅ |

**پاسخ Wallex:**

```json
{
  "message": "اطلاعات وارد شده اشتباه‌است.",
  "code": 422,
  "result": {
    "error_code": [1007],
    "stop_price": ["فیلد قیمت توقف الزامی است."]
  }
}

علت ریشه‌ای

Wallex API از stop_Price (P بزرگ + underscore) استفاده می‌کنه.
ما از camelCase (stopPrice) استفاده می‌کردیم که از DevTools تقلید کرده بودیم.

نکته مهم: DevTools نمایش سمت کلاینت والکس رو نشون می‌ده که ممکنه با اسم واقعی فیلد در API فرق کنه.
راه‌حل
python

# قبل (اشتباه):
body["stopPrice"] = str(request.stop_price)
body["stopPriceCondition"] = request.stop_price_condition

# بعد (درست):
body["stop_Price"] = str(request.stop_price)
body["stop_PriceCondition"] = request.stop_price_condition

تست موفق
bash

✅ BUY  STOP_LIMIT با <=  → status=NEW, active=True
✅ SELL STOP_LIMIT با >=  → status=NEW, active=True

سفارش واقعی از UI:
فیلد	مقدار
بازار	PEPE/TMN
سمت	خرید
نوع	حد ضرر (Stop-Limit)
مقدار	100,000 PEPE
قیمت توقف	1.11 <=
قیمت واحد	1.12 TMN
مبلغ کل	112,000 TMN

سفارش در پنل والکس ظاهر شد و قابل مدیریت است. ✅
درس‌های آموخته

۱. مستندات رسمی رو جدی بگیر — Wallex دقیقاً stop_Price نوشته بود. ما به DevTools اعتماد کردیم.

۲. DevTools فقط سمت کلاینت رو نشون می‌ده — نمایش داده ممکنه با اسم واقعی فیلد در API فرق کنه.

۳. خطای دقیق رو بخون — "فیلد قیمت توقف الزامی است" واضح می‌گفت که فیلد توقف گم شده، یعنی اسمش غلطه، نه مقدارش.

۴. httpx خام ابزار قدرتمنده — وقتی abstraction ما خطا می‌ده، تست مستقیم می‌تونه مشکل رو ایزوله کنه.
قدم‌های بعدی

    پشتیبانی از STOP_MARKET

    تست SELL STOP_LIMIT در سناریوی واقعی

    Alert وقتی stop trigger می‌شه

پایان گزارش
