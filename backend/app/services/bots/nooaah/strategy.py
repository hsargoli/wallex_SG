"""Nooaah strategy — منطق خالص انتخاب و پیشنهاد معامله.

هیچ I/O، هیچ exchange call. فقط تصمیم روی داده‌ی آماده.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.analysis.entities.regime import RegimeResult, RegimeType
from app.domain.entities.candle import Candle
from app.infrastructure.analysis.rule_based_classifier import RuleBasedClassifier
from app.services.bots.nooaah.config import NooaahConfig


@dataclass(frozen=True, slots=True)
class TradeProposal:
    """پیشنهاد معامله برای یه نماد."""

    symbol: str
    action: str  # "BUY" | "WAIT"
    entry: float
    take_profit: float
    stop_loss: float
    confidence: int
    regime: str
    reason: str
    size_mult: float = 1.0  # B1: ضریب حجم


def _confirmed_regime(
    candles: Sequence[Candle],
    config: NooaahConfig,
    classifier: RuleBasedClassifier,
) -> "RegimeResult | None":
    """چک کن آخرین N کندل trending_up بوده.

    برای جلوگیری از whipsaw در رنج: لازمه N کندل متوالی trending_up
    باشه، نه فقط آخرین کندل.

    Return: آخرین RegimeResult اگه همه شرط‌ها OK، وگرنه None.
    """
    n = max(config.confirmation_candles, 1)
    latest = None
    for offset in range(n):
        end = len(candles) - offset
        if end < config.min_candles:
            return None
        window = candles[max(0, end - config.context_candles) : end]
        r = classifier.classify(window)
        if r.regime != RegimeType.TRENDING_UP:
            return None
        if not r.is_tradeable:
            return None
        if r.confidence < config.min_confidence:
            return None
        if offset == 0:
            latest = r
    return latest


def _recent_trending_up_ratio(
    candles: Sequence[Candle],
    config: NooaahConfig,
    classifier: RuleBasedClassifier,
) -> float:
    """نسبت trending_up در N کندل اخیر (شبیه‌سازی گذشته).

    برای هر offset از 0 تا N-1، پنجره‌ی context را classify می‌کنیم
    و می‌بینیم چند تا trending_up بوده.
    """
    n = config.regime_filter_window
    if n <= 0:
        return 1.0
    tu = 0
    total = 0
    for offset in range(n):
        end = len(candles) - offset
        if end < config.min_candles:
            break
        window = candles[max(0, end - config.context_candles) : end]
        r = classifier.classify(window)
        if r.regime == RegimeType.TRENDING_UP:
            tu += 1
        total += 1
    return tu / total if total > 0 else 0.0


def _aggregate_to_4h(candles: Sequence[Candle]) -> list[Candle]:
    """هر ۴ کندل 1h → ۱ کندل 4h (exact)."""
    out: list[Candle] = []
    n = len(candles)
    # از آخر به عقب که همیشه ۴تایی کامل داشته باشیم
    for i in range(0, n - 3, 4):
        chunk = candles[i : i + 4]
        out.append(
            Candle(
                time=chunk[0].time,
                open=chunk[0].open,
                high=max(c.high for c in chunk),
                low=min(c.low for c in chunk),
                close=chunk[-1].close,
                volume=sum(c.volume for c in chunk),
            )
        )
    return out


def propose_trade(
    symbol: str,
    candles: Sequence[Candle],
    config: NooaahConfig,
) -> TradeProposal | None:
    """پیشنهاد معامله — یا None اگه شرایط ورود نیست.

    شرایط ورود:
      - regime == TRENDING_UP
      - is_tradeable == True
      - confidence >= config.min_confidence
      - N کندل متوالی trending_up (confirmation_candles)
    """
    if len(candles) < config.min_candles:
        return None

    classifier = RuleBasedClassifier()
    result = _confirmed_regime(candles, config, classifier)
    if result is None:
        return None

    # regime filter: نسبت trending_up اخیر
    if config.regime_filter_window > 0:
        ratio = _recent_trending_up_ratio(candles, config, classifier)
        if ratio < config.regime_filter_min_ratio:
            return None

    # Volume filter (A2)
    if config.volume_z_min > -10.0:
        from app.domain.analysis.models.feature_math import volume_z as _vz
        vz = _vz(list(candles[-config.context_candles :]))
        if vz < config.volume_z_min:
            return None

    # RSI filter (A1)
    if config.rsi_entry_max < 100.0 or config.rsi_entry_min > 0.0:
        from app.domain.analysis.models.feature_math import rsi as _rsi
        current_rsi = _rsi(list(candles[-config.context_candles :]), 14)
        if current_rsi > config.rsi_entry_max:
            return None
        if current_rsi < config.rsi_entry_min:
            return None

    # A3: 4h confirmation
    if config.use_4h_confirmation:
        candles_4h = _aggregate_to_4h(candles)
        ctx_4h = max(config.context_candles // 4, 50)
        if len(candles_4h) < ctx_4h:
            return None
        r_4h = classifier.classify(candles_4h[-ctx_4h:])
        if r_4h.regime != RegimeType.TRENDING_UP:
            return None
        if not r_4h.is_tradeable:
            return None

    entry = float(candles[-1].close)
    if entry <= 0:
        return None

    atr_pct = (result.atr_pct / 100) if result.atr_pct else 0.01

    # C2: dynamic multiplier based on volatility ratio
    tp_mult = config.tp_atr_mult
    sl_mult = config.sl_atr_mult
    if config.use_dynamic_atr:
        from app.domain.analysis.models.feature_math import volatility as _vol
        short = candles[-config.vol_short_window :]
        long_ = candles[-config.vol_long_window :]
        v_now = _vol(short)
        v_avg = _vol(long_)
        if v_avg > 0:
            ratio = v_now / v_avg
            # clamp 0.5 تا 2.0 که افراط نکنیم
            ratio = max(0.5, min(2.0, ratio))
            tp_mult = config.tp_atr_mult * ratio
            sl_mult = config.sl_atr_mult * ratio

    tp = entry * (1 + tp_mult * atr_pct)
    sl = entry * (1 - sl_mult * atr_pct)

    size_mult = _confidence_mult(result.confidence, config)

    return TradeProposal(
        symbol=symbol,
        action="BUY",
        entry=entry,
        take_profit=tp,
        stop_loss=sl,
        confidence=result.confidence,
        regime=result.regime.value,
        reason=" | ".join(result.reasons),
        size_mult=size_mult,
    )


def _confidence_mult(conf: int, cfg: NooaahConfig) -> float:
    """محاسبه‌ی ضریب حجم از confidence (linear interpolation)."""
    if not cfg.use_confidence_sizing:
        return 1.0
    lo, hi = cfg.conf_sizing_low, cfg.conf_sizing_high
    ml, mh = cfg.size_mult_low, cfg.size_mult_high
    if conf <= lo:
        return ml
    if conf >= hi:
        return mh
    t = (conf - lo) / (hi - lo)
    return ml + t * (mh - ml)


def pick_best(
    proposals: Sequence[TradeProposal | None],
) -> TradeProposal | None:
    """از بین پیشنهادها، بهترین (بالاترین confidence) رو انتخاب کن."""
    valid = [p for p in proposals if p is not None]
    if not valid:
        return None
    return max(valid, key=lambda p: p.confidence)


def decide(
    symbols_candles: dict[str, Sequence[Candle]],
    config: NooaahConfig,
) -> TradeProposal | None:
    """تصمیم نهایی: از دیکشنری نماد→کندل، بهترین پیشنهاد رو بده."""
    proposals = [
        propose_trade(sym, candles, config)
        for sym, candles in symbols_candles.items()
    ]
    return pick_best(proposals)

def should_exit_on_momentum(
    candles_1m: Sequence[Candle],
    window: int = 30,
    red_ratio: float = 0.6,
    mode: str = "ratio",
    consecutive: int = 4,
    cumulative_pct: float = -0.3,
) -> bool:
    """momentum exit — سه معیار.

    - ratio:       ≥ red_ratio از window کندل قرمز
    - consecutive: ≥ consecutive کندل قرمز پشت‌سرهم
    - cumulative:  مجموع تغییرات window کندل < cumulative_pct٪
    """
    if window <= 0 or len(candles_1m) < window:
        return False
    recent = candles_1m[-window:]

    if mode == "ratio":
        reds = sum(1 for c in recent if c.close < c.open)
        return (reds / window) >= red_ratio

    if mode == "consecutive":
        streak = 0
        best = 0
        for c in recent:
            if c.close < c.open:
                streak += 1
                if streak > best:
                    best = streak
            else:
                streak = 0
        return best >= consecutive

    if mode == "cumulative":
        first_close = float(recent[0].close)
        last_close = float(recent[-1].close)
        if first_close <= 0:
            return False
        change_pct = (last_close - first_close) / first_close * 100
        return change_pct < cumulative_pct

    return False

