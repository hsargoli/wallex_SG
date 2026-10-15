"""Guest Token — تولید و اعتبارسنجی UUID v4."""

from __future__ import annotations

import re
import uuid

# الگوی UUID v4 (hex با خط تیره‌ها)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def generate_guest_token() -> str:
    """تولید guest-token جدید (UUID v4).

    Returns:
        str: مثل "a1b2c3d4-e5f6-4789-a012-34567890abcd"
    """
    return str(uuid.uuid4())


def is_valid_token(token: str) -> bool:
    """اعتبارسنجی فرمت guest-token.

    فقط چک فرمت UUID v4 می‌کنه. وجود واقعی توکن توی storage
    وظیفه‌ی لایه‌ی بالاتره.
    """
    if not isinstance(token, str):
        return False
    return bool(_UUID_RE.match(token))


def validate_token(token: str) -> None:
    """مثل is_valid_token، ولی در صورت نامعتبر بودن ValueError می‌دهد.

    Raises:
        ValueError: اگر توکن فرمت UUID v4 نداشته باشد.
    """
    if not is_valid_token(token):
        raise ValueError(f"guest_token نامعتبر است: {token!r}")
