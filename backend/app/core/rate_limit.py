"""Rate limiting با slowapi.

ایده: هر IP یه سهم مشخص درخواست داره. بیشتر از اون → 429.
برای endpointهای حساس (ثبت سفارش) محدودیت سخت‌تر.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter سراسری — همه routerها از این استفاده می‌کنن
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # default برای همه endpoints
    headers_enabled=True,  # اضافه کردن X-RateLimit-* به پاسخ‌ها
)


# ---------- محدودیت‌های اختصاصی ----------
# اینا رو تو endpointها با @limiter.limit(...) استفاده می‌کنیم

PLACE_ORDER_LIMIT = "5/minute"       # ثبت سفارش — سخت‌گیرانه
CANCEL_ORDER_LIMIT = "10/minute"     # لغو سفارش
LIST_ORDERS_LIMIT = "30/minute"      # لیست سفارش‌ها

LOGIN_LIMIT = "5/minute"          # تلاش برای ورود
FORGOT_PASSWORD_LIMIT = "3/minute" # درخواست فراموشی رمز
