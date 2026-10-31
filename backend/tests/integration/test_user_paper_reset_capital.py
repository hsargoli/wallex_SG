"""Reset must create state with 10M capital (per Hosein 2026-10-31)."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestResetCapital:
    def test_paper_state_with_capital_helper(self):
        """PaperState.with_capital(10M) creates correct state."""
        from app.infrastructure.paper_trading.state import PaperState

        s = PaperState.with_capital(10_000_000.0)
        assert s.initial_capital == 10_000_000.0
        assert s.capital == 10_000_000.0
        assert s.equity == 10_000_000.0
        assert s.peak_capital == 10_000_000.0
        assert s.peak_equity == 10_000_000.0
        assert s.total_pnl == 0.0
        assert s.total_pnl_pct == 0.0
