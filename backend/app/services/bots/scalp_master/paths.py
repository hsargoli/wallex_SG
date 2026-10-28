"""Absolute paths for scalp_master runtime data (per-user)."""
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_DIR = _BACKEND / "data" / "bots" / "scalp_master"
USERS_DIR = DATA_DIR / "users"
USERS_DIR.mkdir(parents=True, exist_ok=True)


def user_state_path(user_id: str) -> Path:
    return USERS_DIR / f"{user_id}.json"


def user_audit_path(user_id: str) -> Path:
    return USERS_DIR / f"{user_id}.audit.jsonl"
