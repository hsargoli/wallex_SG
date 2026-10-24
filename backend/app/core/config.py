from dotenv import load_dotenv
load_dotenv()
"""تنظیمات مرکزی برنامه — خواندن از .env در ریشه پروژه."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ریشه پروژه: ~/wallex/
# این فایل: backend/app/core/config.py
# parents[0]=core, parents[1]=app, parents[2]=backend, parents[3]=wallex
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str = "noreply@sarvbots.ir"
    """تنظیمات برنامه با اعتبارسنجی خودکار."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    PROJECT_NAME: str = "Wallex Platform"
    FRONTEND_URL: str = "http://localhost:3020"
    ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Wallex Exchange ---
    WALLEX_BASE_URL: str = "https://api.wallex.ir"
    WALLEX_WS_URL: str = "wss://api.wallex.ir/ws"
    WALLEX_API_KEY: str = Field(..., min_length=10)
    ANALYSIS_CLASSIFIER: str = Field(default="rule_based")
    WALLEX_TIMEOUT_SECONDS: int = Field(default=15, ge=1, le=60)
    WALLEX_MAX_CONNECTIONS: int = Field(default=20, ge=1, le=100)

    # --- Wallex Token Encryption (phase 17.8) ---
    # Fernet key (base64, 44 chars). Empty = encryption disabled (tests only).
    # Validation happens at use-time in app/core/crypto.py, not at startup.
    WALLEX_TOKEN_ENC_KEY: str = ""

    # --- Cache ---
    CACHE_TTL_SECONDS: int = Field(default=5, ge=1, le=3600)

    # --- Trading Safety ---
    LIVE_TRADING_ENABLED: bool = False

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def can_trade(self) -> bool:
        """آیا اجازه معامله واقعی داده میشه؟"""
        return self.LIVE_TRADING_ENABLED


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings به‌صورت singleton — یک بار خوانده می‌شود."""
    return Settings()
