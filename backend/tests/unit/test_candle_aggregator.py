"""Unit tests for candle aggregator."""

from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.candle_aggregator import aggregate_candles


def _make_candle(i: int, base: int = 100, vol: str = "10") -> Candle:
    """کندل ساختگی: open=base+i, high=base+5+i, low=base-5+i, close=base+2+i."""
    return Candle(
        time=1000 + i * 60,
        open=Decimal(base + i),
        high=Decimal(base + 5 + i),
        low=Decimal(base - 5 + i),
        close=Decimal(base + 2 + i),
        volume=Decimal(vol),
    )


class TestAggregateCandles:
    def test_empty_input(self):
        assert aggregate_candles([], factor=15) == []

    def test_factor_one_returns_copy(self):
        candles = [_make_candle(i) for i in range(5)]
        result = aggregate_candles(candles, factor=1)
        assert len(result) == 5
        assert result[0].time == candles[0].time

    def test_factor_zero_returns_copy(self):
        candles = [_make_candle(i) for i in range(5)]
        result = aggregate_candles(candles, factor=0)
        assert len(result) == 5

    def test_aggregate_15_to_1(self):
        candles = [_make_candle(i) for i in range(15)]
        result = aggregate_candles(candles, factor=15)
        assert len(result) == 1
        c = result[0]
        assert c.time == 1000
        assert c.open == Decimal("100")
        assert c.high == Decimal("119")
        assert c.low == Decimal("95")
        assert c.close == Decimal("116")
        assert c.volume == Decimal("150")

    def test_aggregate_4_to_1(self):
        candles = [_make_candle(i) for i in range(8)]
        result = aggregate_candles(candles, factor=4)
        assert len(result) == 2
        assert result[0].time == 1000
        assert result[1].time == 1000 + 4 * 60

    def test_partial_last_group(self):
        # 17 کندل، factor=15 → 2 کندل (یکی 15، یکی 2)
        candles = [_make_candle(i) for i in range(17)]
        result = aggregate_candles(candles, factor=15)
        assert len(result) == 2
        # گروه دوم فقط ۲ کندل داره (i=15, 16)
        assert result[1].time == 1000 + 15 * 60

    def test_unsorted_input_is_sorted(self):
        candles = [_make_candle(i) for i in [3, 1, 0, 2, 4]]
        result = aggregate_candles(candles, factor=5)
        assert len(result) == 1
        assert result[0].time == 1000  # از کندل i=0

    def test_high_low_from_all_group_members(self):
        # اگه high/low وسط گروه بیشتر/کمتر باشه، باید capture بشه
        candles = [
            Candle(
                1000, Decimal("100"), Decimal("110"), Decimal("90"), Decimal("105"), Decimal("1")
            ),
            Candle(
                1060, Decimal("105"), Decimal("200"), Decimal("50"), Decimal("150"), Decimal("1")
            ),
            Candle(
                1120, Decimal("150"), Decimal("160"), Decimal("140"), Decimal("155"), Decimal("1")
            ),
        ]
        result = aggregate_candles(candles, factor=3)
        assert result[0].high == Decimal("200")
        assert result[0].low == Decimal("50")
        assert result[0].open == Decimal("100")
        assert result[0].close == Decimal("155")
