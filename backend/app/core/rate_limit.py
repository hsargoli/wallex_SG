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

# ---------- Fix #3 (2026-10-20) — endpointهای حساس ----------
REGISTER_LIMIT = "3/hour"            # ثبت‌نام — اسپم
RESET_PASSWORD_LIMIT = "5/hour"      # ریست رمز — اسپم
CONNECT_LIMIT = "5/hour"             # اتصال والکس — brute-force
CONNECT_TRADE_LIMIT = "5/hour"       # اتصال توکن معاملات
LOGOUT_ALL_LIMIT = "3/hour"   # خروج از همه دستگاه‌ها
CHANGE_PASSWORD_LIMIT = "5/hour"   # تغییر رمز (JWT + current_password)
