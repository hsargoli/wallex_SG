#!/usr/bin/env python3
"""Paper Mode Watchdog: alert if paper mode > 30 days and still active."""
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.bots.bear_hunter.state import StateStore
from app.services.bots.bear_hunter.paths import USERS_DIR


def check():
    alerts = []
    for f in USERS_DIR.glob("*.json"):
        if f.name.endswith(".audit.jsonl"):
            continue
        try:
            store = StateStore(path=str(f))
            state = store.load()
        except Exception as e:
            alerts.append(f"ERROR loading {f.name}: {e}")
            continue

        if not state.paper_mode:
            continue
        if state.paper_started_at is None:
            continue

        days = (datetime.now(timezone.utc) - state.paper_started_at).days
        if days >= 30 and state.bot_status == "active":
            alerts.append(
                f"ALERT: user={f.stem} paper_mode={days} days old, "
                f"status=active. Consider graduation or abort."
            )

    if alerts:
        for a in alerts:
            print(a)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(check())
