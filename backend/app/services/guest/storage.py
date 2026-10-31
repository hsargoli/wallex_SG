"""Guest Storage — مدیریت مسیرهای per-guest state.

ساختار:
    data/
    ├── paper_v3/
    │   └── state.json              ← کاربر (بدون تغییر)
    └── guests/
        ├── {token-1}/
        │   ├── state.json          ← PaperState مهمان
        │   └── meta.json           ← متادیتا (created_at, last_seen)
        └── {token-2}/
            ├── state.json
            └── meta.json
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.services.guest.token import validate_token

# ریشه‌ی همه‌ی مهمان‌ها
GUEST_ROOT = Path("data/guests")


def guest_dir(token: str) -> Path:
    """مسیر پوشه‌ی یه مهمان.

    Args:
        token: guest-token (UUID v4)

    Returns:
        Path: مثل data/guests/{token}
    """
    validate_token(token)
    return GUEST_ROOT / token


def guest_state_path(token: str) -> Path:
    """مسیر state.json مهمان."""
    return guest_dir(token) / "state.json"


def guest_meta_path(token: str) -> Path:
    """مسیر meta.json مهمان (متادیتا)."""
    return guest_dir(token) / "meta.json"


def ensure_guest_dir(token: str) -> Path:
    """اطمینان از وجود پوشه‌ی مهمان (mkdir -p).

    Returns:
        Path: مسیر پوشه.
    """
    d = guest_dir(token)
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_guests() -> list[str]:
    """لیست همه‌ی guest-tokenهای موجود روی دیسک.

    Returns:
        list[str]: لیست توکن‌ها (فقط پوشه‌ها، نه فایل‌ها).
    """
    if not GUEST_ROOT.exists():
        return []
    return [
        p.name
        for p in GUEST_ROOT.iterdir()
        if p.is_dir() and (p / "state.json").exists()
    ]


def delete_guest(token: str) -> bool:
    """حذف کامل پوشه‌ی یه مهمان.

    Args:
        token: guest-token

    Returns:
        bool: True اگه حذف شد، False اگه وجود نداشت.
    """
    d = guest_dir(token)
    if not d.exists():
        return False
    shutil.rmtree(d)
    return True

def cleanup_stale_guests(
    base_dir: Path | None = None,
    max_age_hours: int = 24,
) -> int:
    """حذف guest stateهایی که از max_age_hours قدیمی‌ترند.

    Args:
        base_dir: مسیر ریشه‌ی مهمان‌ها. پیش‌فرض GUEST_ROOT.
        max_age_hours: سن حداکثر (پیش‌فرض ۲۴ ساعت).

    Returns:
        int: تعداد پوشه‌های حذف‌شده.
    """
    import json
    import time

    root = base_dir if base_dir is not None else GUEST_ROOT
    if not root.exists():
        return 0

    cutoff = time.time() - max_age_hours * 3600
    removed = 0

    for entry in root.iterdir():
        if not entry.is_dir():
            continue

        # Prefer meta.last_seen_at (set by _get_or_create_meta on every request);
        # fall back to dir mtime only if meta is missing/corrupt.
        ts = entry.stat().st_mtime
        meta_path = entry / "meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if isinstance(meta, dict):
                    last_seen = meta.get("last_seen_at")
                    if isinstance(last_seen, (int, float)):
                        ts = float(last_seen)
            except Exception:
                pass  # fallback to mtime

        if ts < cutoff:
            try:
                shutil.rmtree(entry)
                removed += 1
            except OSError:
                continue

    return removed

