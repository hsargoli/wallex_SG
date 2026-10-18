import json
import logging
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class AuditEntry:
    timestamp: str
    approved: bool
    phase: str
    reject_reason: str
    signal_data: dict
    config_snapshot: dict
    state_snapshot: dict
    dry_run_result: Optional[dict] = None

class AuditTrail:
    def __init__(self, file_path: str = "backend/data/bots/bear_hunter/audit.jsonl"):
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def _append(self, entry_dict: dict) -> None:
        line = json.dumps(entry_dict, ensure_ascii=False, default=str) + "\n"
        def _write():
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line)
        try:
            await asyncio.to_thread(_write)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    async def log_entry(self, approved: bool, phase: str, reject_reason: str, signal: Any, config: Any, state: Any, dry_run_result: Any = None) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            approved=approved,
            phase=phase,
            reject_reason=reject_reason,
            signal_data=getattr(signal, "__dict__", str(signal)),
            config_snapshot=getattr(config, "__dict__", str(config)),
            state_snapshot=getattr(state, "to_dict", lambda: str(state))(),
            dry_run_result=getattr(dry_run_result, "__dict__", str(dry_run_result)) if dry_run_result else None
        )
        await self._append({"type": "pre_flight", **asdict(entry)})

    async def log_trade_intent(self, signal: Any, dry_run_result: Any) -> str:
        """WAL Step 1: Log intent BEFORE calling exchange."""
        audit_id = f"intent-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        entry = {
            "type": "trade_intent",
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal": getattr(signal, "__dict__", str(signal)),
            "dry_run": getattr(dry_run_result, "__dict__", str(dry_run_result)) if dry_run_result else None
        }
        await self._append(entry)
        return audit_id

    async def log_trade_success(self, audit_id: str, position: Any) -> None:
        """WAL Step 2: Log success AFTER exchange confirms."""
        entry = {
            "type": "trade_success",
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "position_id": position.position_id,
            "entry_price": str(position.entry_price)
        }
        await self._append(entry)

    async def log_trade_failure(self, audit_id: str, error: str) -> None:
        """WAL Step 2 (alt): Log failure if exchange rejects."""
        entry = {
            "type": "trade_failure",
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error
        }
        await self._append(entry)

audit_trail = AuditTrail()
