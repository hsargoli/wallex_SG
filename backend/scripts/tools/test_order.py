"""اسکریپت تست ثبت و لغو سفارش روی والکس.

⚠️ هشدار: این اسکریپت سفارش **واقعی** ثبت می‌کنه.
   - قیمت ۵۰٪ زیر بازار (غیرقابل پر شدن)
   - مبلغ کم (۱۰۰,۰۰۰ تومان)
   - فوراً لغو می‌شه
"""

import asyncio
import sys
import time
from decimal import Decimal
from pathlib import Path

# اضافه کردن backend/ به sys.path (چون اسکریپت در scripts/tools/ هست)
_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.core.config import get_settings
from app.domain.entities.order import OrderRequest
from app.domain.value_objects.order_enums import OrderSide, OrderType
from app.infrastructure.exchange.wallex.client import WallexExchange


# ---------- تنظیمات ----------
SYMBOL = "BTCTMN"
BUDGET_TMN = Decimal("100000")  # ۱۰۰ هزار تومان
PRICE_DISCOUNT = Decimal("0.5")  # ۵۰٪ زیر market
# -----------------------------


async def main():
    settings = get_settings()

    async with WallexExchange.create(settings) as ex:
        # ۱. قیمت فعلی
        print("=" * 60)
        print("مرحله ۱: دریافت قیمت فعلی")
        print("=" * 60)
        market = await ex.get_market(SYMBOL)
        best_bid = market.stats.bid_price if market.stats else None
        print(f"best_bid: {best_bid:,} TMN")

        if not best_bid:
            print("❌ قیمت bid در دسترس نیست")
            return

        # ۲. محاسبه پارامترها
        print()
        print("=" * 60)
        print("مرحله ۲: محاسبه پارامترهای سفارش")
        print("=" * 60)

        target_price = (best_bid * PRICE_DISCOUNT).quantize(Decimal("1"))
        quantity = (BUDGET_TMN / target_price).quantize(Decimal("0.00000001"))
        notional = quantity * target_price

        print(f"قیمت هدف:    {target_price:,} TMN  ({PRICE_DISCOUNT*100:.0f}% زیر market)")
        print(f"مقدار:       {quantity} BTC")
        print(f"مبلغ کل:     {notional:,.0f} TMN")
        print(f"client_id:   (بعد از تأیید ساخته میشه)")

        # ۳. تأیید کاربر
        print()
        print("=" * 60)
        print("⚠️  آیا سفارش ثبت بشه؟")
        print("=" * 60)
        print("این سفارش:")
        print(f"  - نماد: {SYMBOL}")
        print(f"  - سمت: BUY")
        print(f"  - نوع: LIMIT")
        print(f"  - قیمت: {target_price:,} TMN (غیرقابل پر شدن)")
        print(f"  - مقدار: {quantity} BTC")
        print(f"  - مبلغ درگیر: {notional:,.0f} TMN")
        print(f"  - بلافاصله بعد از تأیید لغو میشه")
        print()

        confirm = input("برای ادامه 'YES' تایپ کن: ").strip()
        if confirm != "YES":
            print("❌ لغو شد")
            return

        # ۴. ثبت سفارش
        print()
        print("=" * 60)
        print("مرحله ۳: ثبت سفارش")
        print("=" * 60)

        client_id = f"test-{int(time.time())}"
        request = OrderRequest(
            symbol=SYMBOL,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=quantity,
            price=target_price,
            client_id=client_id,
        )

        print(f"client_id: {client_id}")
        print("ارسال...")

        try:
            order = await ex.place_order(request)
        except Exception as e:
            print(f"❌ خطا در ثبت: {type(e).__name__}: {e}")
            return

        print(f"✅ سفارش ثبت شد:")
        print(f"   client_id:  {order.client_id}")
        print(f"   status:     {order.status.value}")
        print(f"   active:     {order.active}")
        print(f"   quantity:   {order.orig_qty}")
        print(f"   price:      {order.price:,}")

        # ۵. صبر کوتاه
        print()
        print("⏳ ۳ ثانیه صبر...")
        await asyncio.sleep(3)

        # ۶. لغو سفارش
        print()
        print("=" * 60)
        print("مرحله ۴: لغو سفارش")
        print("=" * 60)

        try:
            canceled = await ex.cancel_order(order.client_id, SYMBOL)
            print(f"✅ سفارش لغو شد:")
            print(f"   client_id:  {canceled.client_id}")
            print(f"   status:     {canceled.status.value}")
            print(f"   active:     {canceled.active}")
        except Exception as e:
            print(f"❌ خطا در لغو: {type(e).__name__}: {e}")
            print(f"⚠️  لطفاً به‌صورت دستی از پنل والکس لغو کن: {order.client_id}")
            return

        print()
        print("=" * 60)
        print("🎉 تست کامل شد — همه چیز کار می‌کنه!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
