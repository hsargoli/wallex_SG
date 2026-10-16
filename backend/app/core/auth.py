"""Auth utilities — bcrypt (password) + JWT (token).

منابع:
- docs/design/AUTH.md v1.1
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# ═══ Config ═══
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
BCRYPT_COST = int(os.getenv("BCRYPT_COST", "12"))

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY تنظیم نشده — .env رو چک کن")

# ═══ Password ═══

def hash_password(plain: str) -> str:
    """Hash پسورد با bcrypt."""
    if not plain:
        raise ValueError("پسورد خالی نیست")
    salt = bcrypt.gensalt(rounds=BCRYPT_COST)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """تأیید پسورد در برابر hash."""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ═══ JWT ═══

def create_user_token(user_id: str, email: str) -> str:
    """ساخت JWT برای کاربر."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": "user",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=JWT_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_user_token(token: str) -> dict[str, Any]:
    """Decode + validate JWT.

    Raises:
        jwt.InvalidTokenError: اگه token نامعتبر یا منقضی باشه
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
