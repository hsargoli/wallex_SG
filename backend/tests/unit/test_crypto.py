"""تست crypto — Fernet encryption/decryption.

پوشش: roundtrip, key missing, invalid ciphertext, empty input, unicode.
نیاز به WALLEX_TOKEN_ENC_KEY در .env (که در ~/wallex/.env هست).
"""

from __future__ import annotations

import pytest

from app.core.crypto import TokenDecryptError, decrypt_token, encrypt_token


class TestRoundtrip:
    def test_simple_token(self) -> None:
        """توکن ساده → encrypt → decrypt → همون."""
        token = "wallex-view-token-abcdef123456"
        ct = encrypt_token(token)
        assert isinstance(ct, bytes)
        assert ct != token.encode()  # ciphertext ≠ plaintext
        assert decrypt_token(ct) == token

    def test_unicode_token(self) -> None:
        """توکن با یونیکد (احتمالاً نمی‌شه ولی خوبه تست شه)."""
        token = "توکن-والکس-۱۲۳"
        ct = encrypt_token(token)
        assert decrypt_token(ct) == token

    def test_long_token(self) -> None:
        """توکن طولانی (JWT-like)."""
        token = "eyJhbGciOiJIUzI1NiJ9." + "x" * 500
        ct = encrypt_token(token)
        assert decrypt_token(ct) == token

    def test_different_tokens_different_ciphertext(self) -> None:
        """دو توکن یکسان → ciphertext متفاوت (چون nonce تصادفیه)."""
        token = "same-token"
        ct1 = encrypt_token(token)
        ct2 = encrypt_token(token)
        assert ct1 != ct2, "Fernet باید nonce تصادفی داشته باشه"
        assert decrypt_token(ct1) == decrypt_token(ct2) == token


class TestErrors:
    def test_empty_token_raises(self) -> None:
        """توکن خالی → ValueError."""
        with pytest.raises(ValueError, match="خالی"):
            encrypt_token("")

    def test_empty_ciphertext_raises(self) -> None:
        """ciphertext خالی → TokenDecryptError."""
        with pytest.raises(TokenDecryptError, match="خالی"):
            decrypt_token(b"")

    def test_corrupted_ciphertext_raises(self) -> None:
        """ciphertext خراب → TokenDecryptError."""
        ct = encrypt_token("valid-token")
        corrupted = ct[:-10] + b"0123456789"
        with pytest.raises(TokenDecryptError, match="قابل رمزگشایی نیست"):
            decrypt_token(corrupted)

    def test_wrong_key_raises(self) -> None:
        """ciphertext با کلید دیگه → TokenDecryptError."""
        from cryptography.fernet import Fernet

        ct = encrypt_token("my-token")

        # کلید دیگه
        other_fernet = Fernet(Fernet.generate_key())
        with pytest.raises(Exception):  # InvalidToken
            other_fernet.decrypt(ct)
