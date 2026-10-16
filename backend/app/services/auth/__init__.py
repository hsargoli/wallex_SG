"""Auth service — register + login logic."""

from app.services.auth.service import (
    AuthError,
    AuthResult,
    login_user,
    register_user,
)

__all__ = ["AuthError", "AuthResult", "register_user", "login_user"]
