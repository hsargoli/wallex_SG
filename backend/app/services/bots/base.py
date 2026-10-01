"""BaseBot — کلاس پایه برای همه‌ی ربات‌ها."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class BotStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(slots=True)
class BotInfo:
    """شناسنامه‌ی یک ربات."""

    slug: str  # "mean_revert"
    name: str  # "کف‌زن"
    name_en: str  # "Mean Revert Bot"
    version: str  # "0.1.0"
    description: str
    tags: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)  # paper, live, backtest
    author: str = "ROSHD_SARV"


class BaseBot(ABC):
    """کلاس پایه‌ی همه‌ی ربات‌ها."""

    @property
    @abstractmethod
    def info(self) -> BotInfo:
        """شناسنامه‌ی ربات."""
        ...

    @property
    @abstractmethod
    def status(self) -> BotStatus:
        """وضعیت فعلی."""
        ...

    @abstractmethod
    async def start(self, exchange) -> dict:
        """شروع ربات."""
        ...

    @abstractmethod
    async def stop(self) -> dict:
        """توقف ربات."""
        ...

    @abstractmethod
    def reset(self) -> dict:
        """ریست کامل state."""
        ...

    @abstractmethod
    def get_status(self) -> dict:
        """وضعیت کامل."""
        ...
