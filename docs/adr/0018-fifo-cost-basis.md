# 0018. FIFO Cost Basis & Real PnL

**Status:** Accepted
**Date:** 2026-10-17
**Deciders:** حسین س، دی

## Context

کاربر View token رو وصل می‌کنه و موجودی واقعی والکس رو می‌بینه. ولی یه سؤال کلیدی بی‌جواب مونده:

> «من الان چقدر سود یا ضرر کردم؟»

برای این جواب، به **قیمت خرید (cost basis)** هر دارایی نیاز داریم.

### کشف مهم در فاز ۱۷.۸

تست روی `444xrlqlc@mozmail.com` نشون داد که **View token به `GET /v1/account/orders` دسترسی داره** — ۲۵ سفارش برگشت با فیلدهای کامل:

- `symbol` — دارایی (مثلاً PEPETMN)
- `side` — BUY / SELL
- `type` — LIMIT / MARKET
- `status` — FILLED / PARTIAL / CANCELLED / NEW
- `executed_qty` — مقدار واقعی معامله‌شده
- `executed_price` — میانگین قیمت اجرا
- `executed_sum` — مجموع (قیمت × مقدار)
- `fee` — کارمزد
- `created_at` — زمان (برای مرتب‌سازی)

**پس PnL واقعی ممکنه، بدون Trade token.**

### چالش الگوریتمی

کاربر در طول زمان چندین بار یه دارایی رو می‌خره و می‌فروشه. برای محاسبه‌ی «میانگین قیمت خریدِ دارایی فعلی»، باید تصمیم بگیریم کدوم خریدها «مصرف شده» و کدوم «باقی مونده».

سه الگوریتم استاندارد:

| الگوریتم | توضیح |
|----------|-------|
| **FIFO** (First In, First Out) | قدیمی‌ترین خرید، اول مصرف می‌شه |
| Weighted Average | میانگین موزون همه‌ی خریدها |
| LIFO (Last In, First Out) | جدیدترین خرید، اول مصرف می‌شه |

## Decision

**FIFO انتخاب شد** — نه Weighted Average.

### چرا FIFO

- **دقت بیشتر:** واقعاً شبیه‌سازی می‌کنه که کاربر کدوم واحدها رو نگه داشته. Weighted Average فرض می‌کنه کاربر همه‌ی واحدها رو «قاطی» کرده (که در واقعیت غلطه).
- **استاندارد مالیاتی:** IRS، HMRC، و اکثر ادارات مالیات FIFO رو به‌عنوان روش پیش‌فرض قبول دارن.
- **قابل حسابرسی:** اگه کاربر بپرسه «چرا این عدد؟»، می‌تونیم دقیقاً بگیم «این خرید از تاریخ X».
- **آماده برای آینده:** اگه بعداً گزارش مالیاتی خواستیم، FIFO درسته.

**هزینه:** پیاده‌سازی پیچیده‌تر (~۱۵۰ خط در برابر ~۵۰ خط).

### الگوریتم

~~~
INPUT:
  orders = همه‌ی سفارش‌های FILLED (یا PARTIAL با executed_qty > 0)
  sorted by created_at ASC

FOR each asset (e.g. PEPETMN):
  queue = []  # صف خریدها: [{qty, unit_cost, ts}, ...]
  
  FOR order IN orders_where_symbol == asset:
    IF order.side == BUY:
      # کارمزد خرید → هزینه‌ی بیشتر → unit_cost بالاتر
      total_cost = order.executed_sum + order.fee
      unit_cost = total_cost / order.executed_qty
      queue.append({qty: order.executed_qty, unit_cost, ts})
    
    ELSE IF order.side == SELL:
      # کارمزد فروش → درآمد کمتر → در محاسبه‌ی PnL لحاظ می‌شه
      remaining_to_sell = order.executed_qty
      
      WHILE remaining_to_sell > 0 AND queue not empty:
        head = queue[0]
        consumed = min(head.qty, remaining_to_sell)
        head.qty -= consumed
        remaining_to_sell -= consumed
        
        IF head.qty == 0:
          queue.pop(0)
      
      # اگه چیزی مونده که توی queue نبود (خرید قبل از تاریخچه):
      # → unknown_cost += remaining_to_sell * order.executed_price
      IF remaining_to_sell > 0:
        UNKNOWN_WARNING  # نمی‌تونیم PnL حساب کنیم
  
  # حالا queue = خریدهای باقی‌مونده (position فعلی)
  total_qty = sum(q.qty for q in queue)
  total_cost = sum(q.qty * q.unit_cost for q in queue)
  avg_cost = total_cost / total_qty IF total_qty > 0
  
  RETURN {
    asset,
    total_qty,
    avg_cost,
    total_cost,
    has_unknown_history,  # اگه خرید قبل از تاریخچه بوده
  }
~~~

### محاسبه‌ی PnL فعلی

~~~
current_value = balance_total * current_market_price
unrealized_pnl = current_value - total_cost
unrealized_pnl_pct = (unrealized_pnl / total_cost) * 100
~~~

### Edge cases (تصمیم‌ها)

| مورد | تصمیم |
|------|-------|
| **سفارش‌های CANCELLED / NEW** | نادیده گرفته می‌شن (فقط FILLED یا PARTIAL با executed_qty > 0) |
| **سفارش‌های PARTIAL** | با executed_qty واقعی و executed_price لحاظ می‌شن |
| **کارمزد BUY** | به total_cost اضافه می‌شه (unit_cost بالاتر) |
| **کارمزد SELL** | در PnL لحاظ می‌شه (درآمد خالص کمتر) |
| **خرید قبل از تاریخچه** | `has_unknown_history = True` → UI هشدار می‌ده، PnL = NULL |
| **انتقال دارایی از بیرون** | مثل «خرید قبل از تاریخچه» (نمی‌تونیم قیمت خرید رو بدونیم) |
| **موجودی صفر با خریدهای باز** | PnL = خالص سود/ضرر محقق‌شده (realized) |
| **Dust (موجودی خیلی کم)** | نمایش داده می‌شه، ولی اگه total_qty < 1e-8 → صفر در نظر گرفته می‌شه |

### API

~~~
GET /v1/user/wallex/pnl
Auth: JWT

Response:
{
  "assets": [
    {
      "asset": "PEPE",
      "symbol": "PEPETMN",
      "total_qty": "4795673.582",
      "avg_cost": "1.0329",
      "total_cost": "4954421",
      "current_price": "1.04",
      "current_value": "4987500",
      "unrealized_pnl": "33079",
      "unrealized_pnl_pct": "0.66",
      "has_unknown_history": false
    },
    ...
  ],
  "summary": {
    "total_cost": "4954421",
    "total_value": "4987500",
    "total_pnl": "33079",
    "total_pnl_pct": "0.66",
    "assets_with_unknown_history": 0
  },
  "computed_at": "2026-10-17T16:30:00+00:00"
}
~~~

**کش:** ۵ دقیقه (چون get_orders سنگینه؛ orders کاربر سریع عوض نمی‌شن)

### ذخیره‌سازی

**هیچ چیز ذخیره نمی‌شه.** هر بار که endpoint صدا زده می‌شه:
1. `get_orders()` از Wallex
2. FIFO محاسبه
3. برگردون

**دلیل:** 
- قیمت خرید منبع حقیقتش Wallex ـه، نه ما
- اگه user یه سفارش جدید بزنه، ما نمی‌دونیم (View token فقط خواندنیه)
- ذخیره کردن یعنی state که ممکنه stale بشه
- cache (5 min) کافیه برای عملکرد

### Performance

`get_orders()` برای کاربر با ۱۰۰۰ سفارش، ممکنه ~۲ ثانیه طول بکشه. cache (5 min) اون رو قابل قبول می‌کنه.

**آینده (اگه لازم شد):** صفحه‌بندی `get_orders` رو با `limit` + `offset` بهتر می‌کنیم، یا فقط سفارش‌های ۹۰ روز اخیر رو می‌گیریم.

## Consequences

- **Positive:**
  - دقت بالا (واقعاً FIFO رو شبیه‌سازی می‌کنه)
  - استاندارد مالیاتی
  - قابل حسابرسی (می‌تونیم بگیم کدوم خرید مصرف شده)
  - آماده برای گزارش‌های آینده

- **Negative:**
  - پیاده‌سازی پیچیده‌تر (~۱۵۰ خط)
  - تست بیشتر لازمه (FIFO edge cases)
  - کندتر از weighted average (الگوریتم O(n) در برابر O(1))

- **Neutral:**
  - API cache (5 min) کندی رو جبران می‌کنه
  - هیچ DB schema تغییر نمی‌کنه

## References

- ADR 0017 — Wallex View Token
- `app/infrastructure/exchange/wallex/client.py` — `get_orders()`
- `app/domain/entities/order.py` — `Order` entity (fields کامل)
- کشف کلیدی: View token به `/v1/account/orders` دسترسی داره
- AI_PRIMER v2.5 — شاهد، test-first، E2E با مرورگر
