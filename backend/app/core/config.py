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
    """تنظیمات برنامه با اعتبارسنجی خودکار."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    PROJECT_NAME: str = "Wallex Platform"
    ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Wallex Exchange ---
    WALLEX_BASE_URL: str = "https://api.wallex.ir"
    WALLEX_WS_URL: str = "wss://api.wallex.ir/ws"
    WALLEX_API_KEY: str = Field(..., min_length=10)
    WALLEX_TIMEOUT_SECONDS: int = Field(default=10, ge=1, le=60)
    WALLEX_MAX_CONNECTIONS: int = Field(default=20, ge=1, le=100)

    # --- Cache ---
    CACHE_TTL_SECONDS: int = Field(default=5, ge=1, le=3600)

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings به‌صورت singleton — یک بار خوانده می‌شود."""
    return Settings()
