"""Key Levels — محاسبه‌ی سطوح کلیدی.

شامل:
  - Pivot Points (کلاسیک)
  - Support/Resistance خودکار از swing points
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.candle import Candle


@dataclass(slots=True)
class PivotLevels:
    """سطوح Pivot Point برای یک دوره."""
    pp: Decimal  # Pivot Point
    r1: Decimal
    r2: Decimal
    r3: Decimal
    s1: Decimal
    s2: Decimal
    s3: Decimal
    basis_high: Decimal
    basis_low: Decimal
    basis_close: Decimal


@dataclass(slots=True)
class SwingLevel:
    """یک سطح Support/Resistance."""
    price: Decimal
    type: str  # "support" یا "resistance"
    touches: int  # چند بار قیمت بهش واکنش داده
    last_time: int
    strength: str  # "weak" / "medium" / "strong"


def pivot_points(high: Decimal, low: Decimal, close: Decimal) -> PivotLevels:
    """محاسبه‌ی Pivot Points کلاسیک از H، L، C."""
    pp = (high + low + close) / Decimal(3)
    r1 = 2 * pp - low
    s1 = 2 * pp - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2 * (pp - low)
    s3 = low - 2 * (high - pp)
    return PivotLevels(
        pp=pp, r1=r1, r2=r2, r3=r3, s1=s1, s2=s2, s3=s3,
        basis_high=high, basis_low=low, basis_close=close,
    )


def pivot_from_candles(candles: list[Candle]) -> PivotLevels | None:
    """Pivot بر اساس بازه‌ی داده‌شده (کل بازه)."""
    if not candles:
        return None
    high = max(c.high for c in candles)
    low = min(c.low for c in candles)
    close = candles[-1].close
    return pivot_points(high, low, close)


def find_swing_levels(
    candles: list[Candle],
    lookback: int = 5,
    tolerance_pct: float = 0.5,
) -> list[SwingLevel]:
    """پیدا کردن Support/Resistance خودکار.

    روش:
      1. swing high/low محلی رو پیدا کن (fractal)
      2. سطوح نزدیک به هم رو ادغام کن (tolerance)
      3. هر سطح چند بار لمس شده؟
    """
    if len(candles) < lookback * 2 + 1:
        return []

    # ---------- ۱. Swing points ----------
    swing_highs: list[tuple[int, Decimal]] = []
    swing_lows: list[tuple[int, Decimal]] = []

    for i in range(lookback, len(candles) - lookback):
        c = candles[i]
        window = candles[i - lookback : i + lookback + 1]

        # swing high: بالاترین high در پنجره
        if c.high == max(x.high for x in window):
            swing_highs.append((c.time, c.high))
        # swing low: پایین‌ترین low در پنجره
        if c.low == min(x.low for x in window):
            swing_lows.append((c.time, c.low))

    # ---------- ۲. ادغام سطوح نزدیک ----------
    def cluster(points: list[tuple[int, Decimal]], kind: str) -> list[SwingLevel]:
        if not points:
            return []
        sorted_pts = sorted(points, key=lambda x: x[1])
        groups: list[list[tuple[int, Decimal]]] = []
        current = [sorted_pts[0]]

        for p in sorted_pts[1:]:
            ref = current[0][1]
            if ref > 0 and abs(p[1] - ref) / ref * Decimal(100) <= Decimal(str(tolerance_pct)):
                current.append(p)
            else:
                groups.append(current)
                current = [p]
        groups.append(current)

        levels: list[SwingLevel] = []
        for group in groups:
            avg_price = sum(p[1] for p in group) / Decimal(len(group))
            last_time = max(p[0] for p in group)
            touches = len(group)
            if touches >= 4:
                strength = "strong"
            elif touches >= 2:
                strength = "medium"
            else:
                strength = "weak"
            levels.append(
                SwingLevel(
                    price=avg_price,
                    type=kind,
                    touches=touches,
                    last_time=last_time,
                    strength=strength,
                )
            )
        return levels

    supports = cluster(swing_lows, "support")
    resistances = cluster(swing_highs, "resistance")

    # فقط قوی‌ترین‌ها
    supports = sorted(supports, key=lambda x: (-x.touches, -x.price))[:5]
    resistances = sorted(resistances, key=lambda x: (-x.touches, x.price))[:5]

    return supports + resistances
