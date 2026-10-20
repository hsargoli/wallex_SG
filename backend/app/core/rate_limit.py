"""Rate limiting با slowapi.

ایده: هر IP یه سهم مشخص درخواست داره. بیشتر از اون → 429.
برای endpointهای حساس (ثبت سفارش) محدودیت سخت‌تر.
"""

from slowapi import Limiter
from fastapi import Request
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
def get_user_and_ip(request: Request) -> str:
    """کلید ترکیبی user_id:ip برای Rate Limit.

    چرا؟ جلوگیری از دور زدن محدودیت با تغییر IP (مهاجم با ۱۰ IP، ۱۰ برابر شانس).
    اگر توکن معتبر نبود، از anon:ip استفاده می‌کنیم.
    """
    import jwt
    from fastapi import Request
    from app.core.auth import decode_user_token
    from app.core.rate_limit import get_remote_address

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = decode_user_token(token)
            user_id = payload.get("sub", "anon")
            ip = get_remote_address(request)
            return f"{user_id}:{ip}"
        except jwt.InvalidTokenError:
            pass  # توکن نامعتبر/منقضی
        except Exception:
            pass

    # fallback برای کاربران ناشناس
    ip = get_remote_address(request)
    return f"anon:{ip}"
