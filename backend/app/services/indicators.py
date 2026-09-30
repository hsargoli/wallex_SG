"""Indicators — محاسبه‌ی اندیکاتورهای تکنیکال از کندل‌ها.

هر تابع لیست Candle می‌گیره و لیست مقادیر (با None برای ابتدای کار)
برمی‌گردونه که طولش با ورودی یکسانه.
"""

from decimal import Decimal

from app.domain.entities.candle import Candle

Num = Decimal | None


def sma(candles: list[Candle], period: int) -> list[Num]:
    """Simple Moving Average — میانگین متحرک ساده.

    Args:
        candles: لیست کندل‌ها (مرتب بر اساس زمان صعودی)
        period: طول دوره

    Returns:
        لیستی با همون طول ورودی. برای idx < period-1 مقدار None است.
    """
    if period <= 0:
        raise ValueError("period must be positive")

    closes = [c.close for c in candles]
    result: list[Num] = [None] * len(candles)
    if len(candles) < period:
        return result

    window_sum = sum(closes[:period], Decimal(0))
    result[period - 1] = window_sum / Decimal(period)

    for i in range(period, len(candles)):
        window_sum = window_sum - closes[i - period] + closes[i]
        result[i] = window_sum / Decimal(period)

    return result


def ema(candles: list[Candle], period: int) -> list[Num]:
    """Exponential Moving Average — میانگین متحرک نمایی."""
    if period <= 0:
        raise ValueError("period must be positive")

    closes = [c.close for c in candles]
    result: list[Num] = [None] * len(candles)
    if len(candles) < period:
        return result

    multiplier = Decimal(2) / Decimal(period + 1)

    # مقدار اول: SMA of first `period`
    seed = sum(closes[:period], Decimal(0)) / Decimal(period)
    result[period - 1] = seed

    for i in range(period, len(candles)):
        prev = result[i - 1]
        assert prev is not None
        result[i] = (closes[i] - prev) * multiplier + prev

    return result


def rsi(candles: list[Candle], period: int = 14) -> list[Num]:
    """Relative Strength Index — شاخص قدرت نسبی.

    مقادیر بین ۰ تا ۱۰۰:
    - > 70: بیش‌خرید
    - < 30: بیش‌فروش
    """
    if period <= 0:
        raise ValueError("period must be positive")

    closes = [c.close for c in candles]
    result: list[Num] = [None] * len(candles)
    if len(candles) < period + 1:
        return result

    # میانگین سود/ضرر اولیه
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        gains.append(change if change > 0 else Decimal(0))
        losses.append(-change if change < 0 else Decimal(0))

    avg_gain = sum(gains, Decimal(0)) / Decimal(period)
    avg_loss = sum(losses, Decimal(0)) / Decimal(period)

    if avg_loss == 0:
        result[period] = Decimal(100)
    else:
        rs = avg_gain / avg_loss
        result[period] = Decimal(100) - (Decimal(100) / (Decimal(1) + rs))

    # محاسبه‌ی Wilders smoothing
    for i in range(period + 1, len(candles)):
        change = closes[i] - closes[i - 1]
        gain = change if change > 0 else Decimal(0)
        loss = -change if change < 0 else Decimal(0)

        avg_gain = (avg_gain * Decimal(period - 1) + gain) / Decimal(period)
        avg_loss = (avg_loss * Decimal(period - 1) + loss) / Decimal(period)

        if avg_loss == 0:
            result[i] = Decimal(100)
        else:
            rs = avg_gain / avg_loss
            result[i] = Decimal(100) - (Decimal(100) / (Decimal(1) + rs))

    return result


def volume_sma(candles: list[Candle], period: int = 20) -> list[Num]:
    """میانگین متحرک حجم."""
    if period <= 0:
        raise ValueError("period must be positive")

    volumes = [c.volume for c in candles]
    result: list[Num] = [None] * len(candles)
    if len(candles) < period:
        return result

    window_sum = sum(volumes[:period], Decimal(0))
    result[period - 1] = window_sum / Decimal(period)

    for i in range(period, len(candles)):
        window_sum = window_sum - volumes[i - period] + volumes[i]
        result[i] = window_sum / Decimal(period)

    return result


def macd(
    candles: list[Candle],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[list[Num], list[Num], list[Num]]:
    """MACD — Moving Average Convergence Divergence.

    Returns:
        (macd_line, signal_line, histogram)
    """
    ema_fast = ema(candles, fast)
    ema_slow = ema(candles, slow)

    macd_line: list[Num] = []
    for f, s in zip(ema_fast, ema_slow, strict=False):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)

    # سیگنال = EMA روی MACD
    # چون MACD خودش EMA-like هست، اینجا از میانگین ساده استفاده می‌کنیم
    signal_line: list[Num] = [None] * len(candles)
    valid_start = slow + signal_period - 1
    if len(candles) >= valid_start:
        for i in range(valid_start - 1, len(candles)):
            window = [v for v in macd_line[i - signal_period + 1 : i + 1] if v is not None]
            if len(window) == signal_period:
                signal_line[i] = sum(window, Decimal(0)) / Decimal(signal_period)

    histogram: list[Num] = []
    for m, s in zip(macd_line, signal_line, strict=False):
        if m is None or s is None:
            histogram.append(None)
        else:
            histogram.append(m - s)

    return macd_line, signal_line, histogram


def bollinger(
    candles: list[Candle],
    period: int = 20,
    num_std: Decimal = Decimal(2),
) -> tuple[list[Num], list[Num], list[Num]]:
    """Bollinger Bands.

    Returns:
        (upper, middle, lower)
    """
    middle = sma(candles, period)
    upper: list[Num] = [None] * len(candles)
    lower: list[Num] = [None] * len(candles)

    closes = [c.close for c in candles]
    for i in range(period - 1, len(candles)):
        window = closes[i - period + 1 : i + 1]
        m = middle[i]
        if m is None:
            continue
        variance = sum((x - m) ** 2 for x in window) / Decimal(period)
        std = variance.sqrt()
        upper[i] = m + num_std * std
        lower[i] = m - num_std * std

    return upper, middle, lower


def atr(candles: list[Candle], period: int = 14) -> list[Num]:
    """Average True Range — نوسان‌سنج."""
    if period <= 0:
        raise ValueError("period must be positive")

    result: list[Num] = [None] * len(candles)
    if len(candles) < period + 1:
        return result

    trs: list[Decimal] = []
    for i in range(1, len(candles)):
        high = candles[i].high
        low = candles[i].low
        prev_close = candles[i - 1].close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)

    # ATR اولیه
    first_atr = sum(trs[:period], Decimal(0)) / Decimal(period)
    result[period] = first_atr

    # Wilder's smoothing
    prev = first_atr
    for i in range(period + 1, len(candles)):
        tr = trs[i - 1]
        prev = (prev * Decimal(period - 1) + tr) / Decimal(period)
        result[i] = prev

    return result
