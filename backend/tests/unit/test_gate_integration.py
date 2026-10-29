"""Phase 2A integration: SarvRouter writes gate, nooaah reads gate."""
from decimal import Decimal
import json
import uuid

from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.gate import read_gate
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail


def _c(t, price):
    p = Decimal(str(price))
    return Candle(time=t, open=p, high=p+1, low=p-1, close=p, volume=Decimal("100"))


def _up(n=300):
    return [_c(i*3600, 100 + i*2) for i in range(n)]


def _down(n=300):
    return [_c(i*3600, 700 - i*2) for i in range(n)]


class TestGateIntegration:
    def test_sarv_uptrend_opens_gate(self, tmp_path, monkeypatch):
        import app.services.bots.sarv_router.bot as bot_mod
        gate_path = tmp_path / "gate.json"

        # Patch write_gate to use tmp_path
        from app.services.bots.sarv_router.gate import write_gate as orig_write
        def _write(allow_new_entries, regime, path=None):
            orig_write(allow_new_entries, regime, path=gate_path)
        monkeypatch.setattr(bot_mod, "write_gate", _write)

        router = SarvRouter(
            config=SarvRouterConfig(), start_bot=lambda s: None,
            stop_bot=lambda s: None, stop_all=lambda: None,
            store=SarvStore(base_dir=tmp_path), audit=AuditTrail(base_dir=tmp_path),
        )
        uid = str(uuid.uuid4())
        router.tick(uid, _up(300), now_idx=0)

        g = read_gate(path=gate_path)
        assert g.allow_new_entries is True
        assert g.regime == "uptrend"

    def test_sarv_downtrend_closes_gate(self, tmp_path, monkeypatch):
        import app.services.bots.sarv_router.bot as bot_mod
        gate_path = tmp_path / "gate.json"

        from app.services.bots.sarv_router.gate import write_gate as orig_write
        def _write(allow_new_entries, regime, path=None):
            orig_write(allow_new_entries, regime, path=gate_path)
        monkeypatch.setattr(bot_mod, "write_gate", _write)

        router = SarvRouter(
            config=SarvRouterConfig(), start_bot=lambda s: None,
            stop_bot=lambda s: None, stop_all=lambda: None,
            store=SarvStore(base_dir=tmp_path), audit=AuditTrail(base_dir=tmp_path),
        )
        uid = str(uuid.uuid4())
        router.tick(uid, _down(300), now_idx=0)

        g = read_gate(path=gate_path)
        assert g.allow_new_entries is False
        assert g.regime == "downtrend"
