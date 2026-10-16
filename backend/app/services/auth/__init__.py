"""Auth service — register + login logic."""

from app.services.auth.merge import (
    MergeResult,
    cleanup_guest,
    load_guest_state,
    merge_guest_into_user,
)
from app.services.auth.service import (
    AuthError,
    AuthResult,
    login_user,
    register_user,
)

__all__ = [
    "AuthError",
    "AuthResult",
    "register_user",
    "login_user",
    "MergeResult",
    "load_guest_state",
    "merge_guest_into_user",
    "cleanup_guest",
]
