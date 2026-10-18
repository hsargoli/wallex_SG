"""Absolute paths for bear_hunter runtime data. Works from any cwd."""
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_DIR = _BACKEND / "data" / "bots" / "bear_hunter"
USERS_DIR = DATA_DIR / "users"
USERS_DIR.mkdir(parents=True, exist_ok=True)


def user_state_path(user_id) -> Path:
    return USERS_DIR / f"{user_id}.json"


def user_audit_path(user_id) -> Path:
    return USERS_DIR / f"{user_id}.audit.jsonl"
