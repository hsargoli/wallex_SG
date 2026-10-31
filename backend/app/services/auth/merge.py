"""Merge guest state → user on register.

منابع:
- docs/design/AUTH.md v1.1 — بخش Merge
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from app.services.guest import (
    delete_guest,
    guest_state_path,
    is_valid_token,
)

log = structlog.get_logger("auth.merge")

# پول پایه‌ی کاربر ثبت‌نام‌شده
USER_BASE_CAPITAL = 10_000_000.0  # 10M (per Hosein 2026-10-31)


@dataclass
class MergeResult:
    """نتیجه‌ی merge از guest."""

    capital_total: float = USER_BASE_CAPITAL
    capital_available: float = USER_BASE_CAPITAL
    open_positions: list[dict] = field(default_factory=list)
    closed_trades: list[dict] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    merged: bool = False


def load_guest_state(token: str) -> dict | None:
    """بارگذاری state.json مهمان.

    Returns:
        dict یا None اگه توکن نامعتبر یا فایل نبود.
    """
    if not token or not is_valid_token(token):
        log.info("merge.skip_invalid_token", token=token[:8] if token else None)
        return None

    path = guest_state_path(token)
    if not path.exists():
        log.info("merge.skip_no_state", token=token[:8] + "...")
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        log.warning("merge.load_failed", token=token[:8] + "...", error=str(e))
        return None


def merge_guest_into_user(token: str | None) -> MergeResult:
    """ادغام state مهمان با سرمایه‌ی پایه.

    اگه token داده نشه یا state نباشه → فقط پول پایه.

    Args:
        token: guest-token (اختیاری)

    Returns:
        MergeResult
    """
    if not token:
        return MergeResult()

    state = load_guest_state(token)
    if state is None:
        return MergeResult()

    # ─── پول: 3M + cash مهمان ───
    guest_capital = float(state.get("capital", 0) or 0)
    capital_total = USER_BASE_CAPITAL + max(guest_capital, 0)

    # ─── positions + trades ───
    open_positions = state.get("open_positions") or []
    # PaperState از "recent_trades" استفاده می‌کنه؛ ما به "closed_trades" map می‌کنیم
    closed_trades = state.get("recent_trades") or []
    equity_curve = state.get("equity_curve") or []

    total_trades = int(state.get("total_trades", 0) or 0)
    wins = int(state.get("wins", 0) or 0)
    losses = int(state.get("losses", 0) or 0)

    log.info(
        "merge.loaded",
        token=token[:8] + "...",
        guest_capital=guest_capital,
        open_positions=len(open_positions),
        closed_trades=len(closed_trades),
        total_trades=total_trades,
    )

    return MergeResult(
        capital_total=capital_total,
        capital_available=capital_total,
        open_positions=open_positions,
        closed_trades=closed_trades,
        equity_curve=equity_curve,
        total_trades=total_trades,
        wins=wins,
        losses=losses,
        merged=True,
    )


def cleanup_guest(token: str | None, merged: bool) -> None:
    """حذف پوشه‌ی مهمان بعد از merge موفق."""
    if not merged or not token:
        return
    if not is_valid_token(token):
        return
    try:
        deleted = delete_guest(token)
        if deleted:
            log.info("merge.guest_cleaned", token=token[:8] + "...")
    except Exception as e:
        log.warning("merge.cleanup_failed", token=token[:8] + "...", error=str(e))
