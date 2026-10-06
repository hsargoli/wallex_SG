"""Volatility Scorer — امتیازدهی نوسان ترکیبی."""

from dataclasses import dataclass
from statistics import mean, stdev

from app.domain.entities.candle import Candle


@dataclass(slots=True)
class VolatilityScore:
    """امتیاز نوسان یک نماد."""

    symbol: str
    total_score: float  # 0-100
    atr_pct: float
    std_returns: float
    range_pct: float
    volume_ratio: float
    score_atr: float
    score_std: float
    score_range: float
    score_vol: float


def _atr_pct(candles: list[Candle], period: int = 14) -> float:
    """ATR% (میانگین دامنه واقعی)."""
    if len(candles) < period + 1:
        return 0.0
    
    trs = []
    for i in range(1, len(candles)):
        h = float(candles[i].high)
        l = float(candles[i].low)
        prev_c = float(candles[i-1].close)
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    
    if not trs:
        return 0.0
    
    recent = trs[-period:]
    avg_tr = mean(recent)
    current_price = float(candles[-1].close)
    
    if current_price == 0:
        return 0.0
    
    return avg_tr / current_price * 100


def _std_returns(candles: list[Candle], period: int = 50) -> float:
    """انحراف معیار بازده."""
    if len(candles) < 2:
        return 0.0
    
    prices = [float(c.close) for c in candles]
    recent = prices[-period:] if len(prices) >= period else prices
    
    if len(recent) < 2:
        return 0.0
    
    returns = [
        (recent[i] / recent[i-1] - 1) * 100
        for i in range(1, len(recent))
        if recent[i-1] != 0
    ]
    
    if len(returns) < 2:
        return 0.0
    
    return stdev(returns)


def _range_pct(candles: list[Candle], period: int = 50) -> float:
    """میانگین دامنه (high-low)/close."""
    if not candles:
        return 0.0
    
    recent = candles[-period:] if len(candles) >= period else candles
    
    ranges = [
        (float(c.high) - float(c.low)) / float(c.close) * 100
        for c in recent
        if float(c.close) > 0
    ]
    
    if not ranges:
        return 0.0
    
    return mean(ranges)


def _volume_ratio(candles: list[Candle], short: int = 20, long: int = 100) -> float:
    """نسبت حجم اخیر به حجم بلندمدت."""
    if len(candles) < long:
        return 1.0
    
    vols = [float(c.volume) for c in candles]
    avg_short = mean(vols[-short:])
    avg_long = mean(vols[-long:])
    
    if avg_long == 0:
        return 1.0
    
    return avg_short / avg_long


@dataclass(slots=True)
class ScorerConfig:
    """تنظیمات امتیازدهی."""

    max_atr_pct: float = 3.0
    max_std: float = 2.0
    max_range: float = 5.0
    max_vol_ratio: float = 3.0

    w_atr: float = 0.35
    w_std: float = 0.25
    w_range: float = 0.25
    w_vol: float = 0.15

    min_candles: int = 50


def calculate_score(
    symbol: str,
    candles: list[Candle],
    config: ScorerConfig | None = None,
) -> VolatilityScore | None:
    """محاسبه امتیاز نوسان."""
    cfg = config or ScorerConfig()
    
    if len(candles) < cfg.min_candles:
        return None
    
    atr_pct = _atr_pct(candles)
    std_ret = _std_returns(candles)
    range_pct = _range_pct(candles)
    vol_ratio = _volume_ratio(candles)
    
    # نرمال‌سازی (0-1)
    score_atr = min(atr_pct / cfg.max_atr_pct, 1.0)
    score_std = min(std_ret / cfg.max_std, 1.0)
    score_range = min(range_pct / cfg.max_range, 1.0)
    score_vol = min(vol_ratio / cfg.max_vol_ratio, 1.0)
    
    # ترکیب وزنی
    total = (
        cfg.w_atr * score_atr
        + cfg.w_std * score_std
        + cfg.w_range * score_range
        + cfg.w_vol * score_vol
    ) * 100  # به 0-100
    
    return VolatilityScore(
        symbol=symbol,
        total_score=round(total, 2),
        atr_pct=round(atr_pct, 3),
        std_returns=round(std_ret, 3),
        range_pct=round(range_pct, 3),
        volume_ratio=round(vol_ratio, 3),
        score_atr=round(score_atr, 3),
        score_std=round(score_std, 3),
        score_range=round(score_range, 3),
        score_vol=round(score_vol, 3),
    )
