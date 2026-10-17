"""Token encryption — Fernet (AES-128-CBC + HMAC-SHA256).

هدف: ذخیره‌ی امن توکن Wallex کاربر (phase 17.8).

استفاده:
    enc = encrypt_token("plaintext-token")
    plain = decrypt_token(enc)  # raises TokenDecryptError

کلید: settings.WALLEX_TOKEN_ENC_KEY (Fernet key، 44 char base64)
- اگه خالی باشه → RuntimeError (fail-fast، نه fail-silent)
- اگه نامعتبر باشه → RuntimeError با پیام واضح
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class TokenDecryptError(Exception):
    """توکن قابل رمزگشایی نیست (کلید عوض شده یا داده خراب)."""


def _get_fernet() -> Fernet:
    """Fernet instance از settings. Lazy — فقط وقتی استفاده بشه.

    Raises:
        RuntimeError: اگه WALLEX_TOKEN_ENC_KEY تنظیم نشده باشه
    """
    settings = get_settings()
    key = settings.WALLEX_TOKEN_ENC_KEY
    if not key:
        raise RuntimeError(
            "WALLEX_TOKEN_ENC_KEY تنظیم نشده. "
            "برای استفاده از ذخیره‌ی امن توکن، یه Fernet key بساز و "
            "توی .env قرار بده."
        )
    try:
        return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except Exception as e:
        raise RuntimeError(
            f"WALLEX_TOKEN_ENC_KEY نامعتبر است (باید Fernet key باشه): {e}"
        ) from e


def encrypt_token(plaintext: str) -> bytes:
    """رمزنگاری توکن. خروجی: bytes (قابل ذخیره در BYTEA)."""
    if not plaintext:
        raise ValueError("توکن خالی است")
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt_token(ciphertext: bytes) -> str:
    """رمزگشایی توکن.

    Raises:
        TokenDecryptError: اگه کلید عوض شده یا داده خراب باشه
    """
    if not ciphertext:
        raise TokenDecryptError("ciphertext خالی است")
    try:
        return _get_fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as e:
        raise TokenDecryptError(
            "توکن قابل رمزگشایی نیست — ممکنه کلید رمزنگاری عوض شده باشه. "
            "لطفاً دوباره توکن والکس رو وارد کن."
        ) from e
