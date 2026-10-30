"""Guest Mode — سرویس حالت مهمان.

شامل:
- token: تولید و اعتبارسنجی guest-token (UUID v4)
- storage: مدیریت مسیرهای per-guest state

منابع:
- docs/design/GUEST_MODE.md (v2.1)
"""

from app.services.guest.scheduler import GuestScheduler
from app.services.guest.storage import (
    GUEST_ROOT,
    cleanup_stale_guests,
    delete_guest,
    ensure_guest_dir,
    guest_dir,
    guest_meta_path,
    guest_state_path,
    list_guests,
)
from app.services.guest.token import (
    generate_guest_token,
    is_valid_token,
    validate_token,
)

__all__ = [
    "generate_guest_token",
    "is_valid_token",
    "validate_token",
    "GUEST_ROOT",
    "guest_dir",
    "guest_state_path",
    "guest_meta_path",
    "ensure_guest_dir",
    "list_guests",
    "delete_guest",
    "cleanup_stale_guests",
    "GuestScheduler",
]
