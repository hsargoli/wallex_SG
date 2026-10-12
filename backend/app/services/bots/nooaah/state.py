"""NooaahState — وضعیت ذخیره‌شده‌ی ربات (positions, capital, trades).

JSON persisted. یک فایل برای هر ربات (فعلاً فقط Nooaah).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar

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
class NooaahCycleLog:
    """ثبت یک cycle اجرای ربات."""

    timestamp: int
    status: str  # ok | killed | cooldown | no_capital | error
    action: str  # no_signal | opened | position_held | cooldown | killed | no_capital
    reason_fa: str
    symbols_analyzed: list[str] = field(default_factory=list)
    opened_symbol: str | None = None
    opened_confidence: int | None = None
    closed_count: int = 0


@dataclass(slots=True)
class NooaahState:
    """وضعیت کامل Nooaah."""

    # --- تنظیمات runtime (state machine) ---
    # Values: paper-testing | ready-for-live | live-active | live-paused
    mode: str = "paper-testing"
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

    # --- Cooldown (ADR-0013 live stop) ---
    cooldown_until: int = 0         # تا این timestamp هیچ معامله‌ی جدیدی نه

    # --- Cycle logs ---
    cycle_logs: list[NooaahCycleLog] = field(default_factory=list)

    # --- Live activation (ADR-0011) ---
    paper_started_at: int = 0       # شروع دوره‌ی paper-testing
    activated_live_at: int = 0      # زمان live-active شدن
    consecutive_losses: int = 0     # برای auto-pause
    live_stage: int = 1             # 1, 2, 3 (staged rollout)
    pause_reason: str = ""          # دلیل auto-pause (اگه live-paused)
    kill_activations_7d: int = 0    # برای condition
    daily_loss_hits_7d: int = 0     # برای condition

    # --- Runtime config (ADR-0012) ---
    # پارامترهای استراتژی + مدیریت — scheduler از این می‌خونه
    runtime_config: dict[str, Any] = field(default_factory=dict)
    # draft برای wizard فعال‌سازی (partial save بین مراحل)
    draft_config: dict[str, Any] = field(default_factory=dict)

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
            # ADR-0011
            "paper_started_at": self.paper_started_at,
            "activated_live_at": self.activated_live_at,
            "consecutive_losses": self.consecutive_losses,
            "live_stage": self.live_stage,
            "pause_reason": self.pause_reason,
            "kill_activations_7d": self.kill_activations_7d,
            "daily_loss_hits_7d": self.daily_loss_hits_7d,
            # ADR-0012
            "runtime_config": self.runtime_config,
            "draft_config": self.draft_config,
            "cooldown_until": self.cooldown_until,
            "cycle_logs": [asdict(c) for c in self.cycle_logs[-100:]],
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
        # Backward compat: "paper" → "paper-testing", "live" → "live-active"
        raw_mode = raw.get("mode", "paper-testing")
        if raw_mode == "paper":
            raw_mode = "paper-testing"
        elif raw_mode == "live":
            raw_mode = "live-active"

        return cls(
            mode=raw_mode,
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
            # ADR-0011
            paper_started_at=raw.get("paper_started_at", 0),
            activated_live_at=raw.get("activated_live_at", 0),
            consecutive_losses=raw.get("consecutive_losses", 0),
            live_stage=raw.get("live_stage", 1),
            pause_reason=raw.get("pause_reason", ""),
            kill_activations_7d=raw.get("kill_activations_7d", 0),
            daily_loss_hits_7d=raw.get("daily_loss_hits_7d", 0),
            # ADR-0012
            runtime_config=raw.get("runtime_config", {}),
            draft_config=raw.get("draft_config", {}),
            cooldown_until=raw.get("cooldown_until", 0),
            cycle_logs=[
                NooaahCycleLog(**c) for c in raw.get("cycle_logs", [])
            ],
        )

    # ============================================================
    # Helpers
    # ============================================================
    def reset_daily_if_needed(self) -> bool:
        """اگه روز عوض شده → reset daily_pnl. cooldown جداست."""
        DAY = 86400
        now = int(time.time())
        today = now // DAY
        if self.day_start == 0 or (self.day_start // DAY) != today:
            self.day_start = now
            self.daily_pnl_pct = 0.0
            # daily_loss_hit رو اگه cooldown تموم شده، ریست کن
            if self.cooldown_until and now >= self.cooldown_until:
                self.daily_loss_hit = False
                self.cooldown_until = 0
            return True
        return False

    @property
    def is_active(self) -> bool:
        """آیا ربات می‌تواند معامله کند؟"""
        if self.killed:
            return False
        if self.mode == "live-paused":
            return False
        if self.mode == "ready-for-live":
            return False  # هنوز فعال نشده
        # cooldown ۶ ساعته بعد از daily loss
        if self.cooldown_until and int(time.time()) < self.cooldown_until:
            return False
        return self.mode in ("paper-testing", "live-active")

    @property
    def cooldown_remaining_seconds(self) -> int:
        """چقدر مونده تا تموم شه cooldown (0 = تموم)."""
        if not self.cooldown_until:
            return 0
        remaining = self.cooldown_until - int(time.time())
        return max(0, remaining)

    def enter_cooldown(self, hours: int = 6) -> None:
        """شروع cooldown ۶ ساعته (بعد از daily loss)."""
        self.cooldown_until = int(time.time()) + hours * 3600
        self.daily_loss_hit = True  # برای گزارش

    # ============================================================
    # Live readiness (ADR-0011)
    # ============================================================
    def readiness_checklist(self) -> dict:
        """چک‌لیست شرایط عبور از paper به ready-for-live.

        Return: {conditions: [...], all_met: bool}
        """
        import time as _time
        DAY = 86400
        now = int(_time.time())
        seven_days_ago = now - 7 * DAY

        # tradeهای ۷ روز اخیر
        recent_trades = [
            t for t in self.closed_trades if t.exit_time >= seven_days_ago
        ]
        trade_count = len(recent_trades)
        wins = [t for t in recent_trades if t.return_pct > 0]
        win_rate = (len(wins) / trade_count * 100) if trade_count else 0.0

        # بازده ۷ روز اخیر (مجموع pnl_pct)
        total_return = sum(t.return_pct for t in recent_trades)

        # روز در paper
        if self.paper_started_at == 0:
            days_in_paper = 0
        else:
            days_in_paper = (now - self.paper_started_at) // DAY

        conditions = [
            {
                "key": "days_paper",
                "label": "حداقل ۷ روز در Paper",
                "current": days_in_paper,
                "target": 7,
                "unit": "روز",
                "met": days_in_paper >= 7,
            },
            {
                "key": "trade_count",
                "label": "حداقل ۱۰ معامله",
                "current": trade_count,
                "target": 10,
                "unit": "",
                "met": trade_count >= 10,
            },
            {
                "key": "win_rate",
                "label": "نرخ برد ≥ ۴۰٪",
                "current": round(win_rate, 1),
                "target": 40,
                "unit": "٪",
                "met": win_rate >= 40,
            },
            {
                "key": "return",
                "label": "بازده ۷ روز > ۰٪",
                "current": round(total_return, 2),
                "target": 0,
                "unit": "٪",
                "met": total_return > 0,
            },
            {
                "key": "kill_activations",
                "label": "بدون Kill-Switch در ۷ روز",
                "current": self.kill_activations_7d,
                "target": 0,
                "unit": "",
                "met": self.kill_activations_7d == 0,
            },
            {
                "key": "daily_loss_hits",
                "label": "بدون Daily Loss Hit در ۷ روز",
                "current": self.daily_loss_hits_7d,
                "target": 0,
                "unit": "",
                "met": self.daily_loss_hits_7d == 0,
            },
        ]

        return {
            "conditions": conditions,
            "all_met": all(c["met"] for c in conditions),
            "days_in_paper": days_in_paper,
            "recent_trades_count": trade_count,
            "recent_win_rate": round(win_rate, 1),
            "recent_return": round(total_return, 2),
        }

    def has_position_for(self, symbol: str) -> bool:
        return any(p.symbol == symbol for p in self.open_positions)

    # ============================================================
    # Runtime config (ADR-0012)
    # ============================================================
    DEFAULT_RUNTIME_CONFIG: ClassVar[dict[str, Any]] = {
        "min_confidence": 85,
        "confirmation_candles": 2,
        "tp_atr_mult": 3.0,
        "sl_atr_mult": 1.5,
        "volume_z_min": -0.5,
        "max_concurrent_positions": 1,
        "top_n": 5,
        "capital_total": 0.0,
        "daily_loss_limit_pct": 2.0,
    }

    def get_runtime_config(self) -> dict[str, Any]:
        """پارامترهای نهایی برای scheduler (پیش‌فرض + ذخیره‌شده)."""
        merged = dict(self.DEFAULT_RUNTIME_CONFIG)
        merged.update(self.runtime_config)
        # سرمایه از state بیاد (نه از runtime) — تنها منبع
        merged["capital_total"] = self.capital_total
        merged["daily_loss_limit_pct"] = self.daily_loss_limit_pct
        return merged

    def finalize_draft(self) -> dict[str, Any]:
        """draft رو نهایی کن (merge با defaults) و برگردون."""
        merged = dict(self.DEFAULT_RUNTIME_CONFIG)
        merged.update(self.draft_config)
        return merged
