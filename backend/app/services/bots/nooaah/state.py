"""NooaahState — وضعیت ذخیره‌شده‌ی ربات (positions, capital, trades).

JSON persisted. یک فایل برای هر ربات (فعلاً فقط Nooaah).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

STATE_DIR = Path("data/nooaah")
STATE_FILE = STATE_DIR / "state.json"


@dataclass(slots=True)
class NooaahPosition:
    """پوزیشن باز."""

    client_id: str
    symbol: str
    entry_price: float
    quantity: float
    tp: float
    sl: float
    entry_time: int
    entry_idx: int = 0
    confidence: int = 0
    size_mult: float = 1.0
    capital_used: float = 0.0


@dataclass(slots=True)
class NooaahClosedTrade:
    """معامله‌ی بسته‌شده."""

    client_id: str
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: int
    exit_time: int
    exit_reason: str
    return_pct: float
    pnl: float  # سود/ضرر مطلق
    duration_candles: int
    confidence: int
    mode: str  # paper | live


@dataclass(slots=True)
class NooaahState:
    """وضعیت کامل Nooaah."""

    # --- تنظیمات runtime ---
    mode: str = "paper"  # paper | live
    daily_loss_limit_pct: float = 2.0  # توصیه‌ی ربات

    # --- سرمایه ---
    capital_total: float = 0.0  # بودجه‌ی اختصاص‌داده‌شده توسط کاربر
    capital_available: float = 0.0  # آزاد
    capital_in_use: float = 0.0  # در پوزیشن‌ها

    # --- پوزیشن‌ها ---
    open_positions: list[NooaahPosition] = field(default_factory=list)
    closed_trades: list[NooaahClosedTrade] = field(default_factory=list)

    # --- روزانه ---
    day_start: int = 0  # unix timestamp شروع روز
    daily_pnl_pct: float = 0.0
    daily_loss_hit: bool = False

    # --- kill-switch ---
    killed: bool = False
    killed_at: int = 0

    # --- آخرین اجرا ---
    last_run: int = 0

    # ============================================================
    # Persistence
    # ============================================================
    def save(self, path: Path | None = None) -> None:
        """ذخیره‌ی اتمیک."""
        p = path or STATE_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "mode": self.mode,
            "daily_loss_limit_pct": self.daily_loss_limit_pct,
            "capital_total": self.capital_total,
            "capital_available": self.capital_available,
            "capital_in_use": self.capital_in_use,
            "open_positions": [asdict(pos) for pos in self.open_positions],
            "closed_trades": [asdict(t) for t in self.closed_trades[-200:]],
            "day_start": self.day_start,
            "daily_pnl_pct": self.daily_pnl_pct,
            "daily_loss_hit": self.daily_loss_hit,
            "killed": self.killed,
            "killed_at": self.killed_at,
            "last_run": self.last_run,
        }
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(p)

    @classmethod
    def load(cls, path: Path | None = None) -> "NooaahState":
        """بارگذاری. اگه نبود، state خالی."""
        p = path or STATE_FILE
        if not p.exists():
            return cls()
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()

        positions = [
            NooaahPosition(**pos) for pos in raw.get("open_positions", [])
        ]
        trades = [
            NooaahClosedTrade(**t) for t in raw.get("closed_trades", [])
        ]
        return cls(
            mode=raw.get("mode", "paper"),
            daily_loss_limit_pct=raw.get("daily_loss_limit_pct", 2.0),
            capital_total=raw.get("capital_total", 0.0),
            capital_available=raw.get("capital_available", 0.0),
            capital_in_use=raw.get("capital_in_use", 0.0),
            open_positions=positions,
            closed_trades=trades,
            day_start=raw.get("day_start", 0),
            daily_pnl_pct=raw.get("daily_pnl_pct", 0.0),
            daily_loss_hit=raw.get("daily_loss_hit", False),
            killed=raw.get("killed", False),
            killed_at=raw.get("killed_at", 0),
            last_run=raw.get("last_run", 0),
        )

    # ============================================================
    # Helpers
    # ============================================================
    def reset_daily_if_needed(self) -> bool:
        """اگه روز عوض شده → reset. Return True اگه reset شد."""
        DAY = 86400
        now = int(time.time())
        today = now // DAY
        if self.day_start == 0 or (self.day_start // DAY) != today:
            self.day_start = now
            self.daily_pnl_pct = 0.0
            self.daily_loss_hit = False
            return True
        return False

    @property
    def is_active(self) -> bool:
        """آیا ربات می‌تواند معامله کند؟"""
        if self.killed:
            return False
        if self.daily_loss_hit:
            return False
        return True

    def has_position_for(self, symbol: str) -> bool:
        return any(p.symbol == symbol for p in self.open_positions)
