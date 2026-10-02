# گزارش رفع باگ معماری API Router

**تاریخ (میلادی):** 2026-10-02
**ساعت (میلادی):** 22:44
**تاریخ (شمسی):** 1405/07/10
**ساعت (شمسی):** 22:44
**کامیت:** `98671f3`
**وضعیت:** کامل — ۳۱ تست از فیل به پاس

---

## 🎯 چطور کشف شد؟

در مرحله‌ی ۴ ممیزی (ساختار پوشه‌ها)، تصمیم گرفتیم تست‌ها را اجرا کنیم تا وضعیت پایه را بسنجیم. نتیجه شوک‌آور بود:

31 failed, 45 passed in 0.76s
text


**۳۱ تست از ۷۶ تست فیل بودند** — در حالی که README ادعا می‌کرد «۷۶ تست، ۱۰۰٪ پاس».

---

## 🔍 ریشه‌یابی

جستجو در تست‌های فیل‌شده نشان داد همه‌ی آن‌ها `404 Not Found` برمی‌گردانند:

assert 404 == 422
assert 404 == 200
text


یعنی endpointهایی که تست صدا می‌زد، در app ثبت نشده بودند.

### کشف اول: main.py فقط ۳ router رو include می‌کرد

```python
# app/main.py (قبل از fix)
app.include_router(markets_router, prefix="/v1/markets")
app.include_router(paper_router, prefix="/v1/paper-trading")
app.include_router(sim_router, prefix="/v1/simulation")

اما router.py (master router) یه فایل کامل داشت که ۱۴ router رو include می‌کرد:
python

# app/presentation/api/v1/router.py
router = APIRouter(prefix="/v1")
router.include_router(markets.router)
router.include_router(account.router)
router.include_router(bot.router)
router.include_router(bots.router)
router.include_router(profitability.router)
# ... و ۹ تای دیگه

پس ۱۱ router کاملاً mount نشده بودند:

    profitability, bots, bot, account

    signals, scanner, backtest, scalping

    ml_bottom, replay, paper_trading

کشف دوم: مسیرهای double-prefix

routerهایی که prefix داخلی داشتن (markets, paper_v2)، وقتی با main.py include می‌شدند، مسیرهای عجیبی می‌ساختند:
text

/v1/markets/markets                     ❌ (باید /v1/markets باشه)
/v1/markets/markets/{symbol}           ❌
/v1/paper-trading/paper-v2/status       ❌ (باید /v1/paper-v2/status باشه)

🛠 راه‌حل
۱. اضافه کردن simulation به master router
python

# app/presentation/api/v1/router.py
from app.presentation.api.v1 import (
    # ...
    simulation,
)
router.include_router(simulation.router)

۲. اضافه کردن prefix به simulation
python

# app/presentation/api/v1/simulation.py
# قبل: router = APIRouter()
# بعد:
router = APIRouter(prefix="/simulation", tags=["Simulation"])

۳. بازنویسی main.py
python

# app/main.py (بعد از fix)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.presentation.api.v1.router import router as v1_router

app = FastAPI(title="ROSHD_SARV API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# همه‌ی مسیرهای v1 از طریق master router
app.include_router(v1_router)

@app.get("/")
async def root():
    return {"message": "Welcome to ROSHD_SARV Backend (DDD Architecture)"}

📊 نتیجه
متریک	قبل	بعد
تعداد مسیرهای ثبت‌شده	۲۱	۴۴
مسیرهای double-prefix	۴	۰
تست‌های پاس	۴۵	۷۶
تست‌های فیل	۳۱	۰
فایل‌های تغییر یافته	—	۴
💡 درس‌های آموخته

    READMه دروغ می‌گفت — «۷۶ تست پاس» در حالی که ۳۱ فیل بودند. هیچ‌کس بعد از تغییرات اخیر تست‌ها رو اجرا نکرده بود.

    master router الگوی درستی است — وقتی نیمه‌کاره رها بشه، باعث این نوع باگ میشه. یا باید کلاً استفاده بشه، یا کلاً حذف.

    FastAPI جدید app.routes رو nested نشون میده — _IncludedRouter در نسخه‌های جدید اومده. برای دیدن مسیرهای واقعی باید app.openapi()["paths"] رو چک کرد.

    مسیرهای double-prefix بدترین نوع باگن — چون کار می‌کنن ولی نه از مسیر درست. هیچ‌کس متوجه نمیشه تا وقتی که فرانت یا تست باهاشون کار نکنه.

    test-driven discovery — حتی وقتی تست‌ها قدیمی هستن، اجراشون می‌تونه باگ‌های پنهان رو کشف کنه.

🎯 کامیت
text

98671f3 fix(api): mount all v1 routers via master router

Problem:
- main.py only included 3 routers → 31 tests failed with 404
- Routers with internal prefix produced double-prefix paths

Solution:
- main.py now uses master router from router.py
- simulation.router gets internal prefix '/simulation'

Before: 31 failed, 45 passed
After:  76 passed, 0 failed ✅

4 files changed, 16 insertions(+), 9 deletions(-)

📌 پیشنهاد برای آینده

    CI/CD اضافه کنه — هر push، تست‌ها اجرا بشن

    تست‌های جدید — برای مسیرهایی که تا حالا کسی ندیده (signals، scanner، replay، ...)

    گزارش روزانه — وضعیت تست‌ها باید جزو گزارش باشه

پایان گزارش — نسخه ۱.۰
