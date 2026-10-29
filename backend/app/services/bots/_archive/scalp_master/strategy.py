"""استراتژی Scalp Master — اسکالپ نزولی v2.

منطق:
  ۱. تشخیص سقوط (افت از سقف N کندل اخیر)
  ۲. تشخیص توقف سقوط (۲ کندل سبز پشت سر هم)
  ۳. RSI در محدوده اشباع فروش
  ۴. SL پویا (ATR-based) + TP = 3×ATR
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.indicators import adx, atr, ema, rsi, volume_sma


@dataclass(slots=True)
class ScalpSignal:
    """سیگنال ورود."""

    should_trade: bool
    action: str
    entry_price: float
    take_profit: float
    stop_loss: float
    reason: str
    drop_pct: float
    rsi: float
    atr_pct: float


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def _drop_pct_at(candles, idx, lookback_high):
    if idx < lookback_high:
        return 0.0
    window = candles[idx - lookback_high + 1:idx + 1]
    recent_high = max(float(c.high) for c in window)
    current = float(candles[idx].close)
    if recent_high <= 0:
        return 0.0
    return (recent_high - current) / recent_high * 100.0


def _is_fresh_dip(candles, config):
    if len(candles) < config.lookback_high + 2:
        return False
    curr = _drop_pct_at(candles, len(candles) - 1, config.lookback_high)
    prev = _drop_pct_at(candles, len(candles) - 2, config.lookback_high)
    return curr >= config.drop_threshold_pct and prev < config.drop_threshold_pct


def _count_recent_greens(candles, limit=10):
    count = 0
    for c in reversed(candles):
        if float(c.close) > float(c.open):
            count += 1
            if count >= limit:
                break
        else:
            break
    return count


def _build_confirmation_signal(candles, config, drop_pct):
    current = candles[-1]
    entry = float(current.close)
    atr_vals = atr(candles, 14)
    atr_val = _last(atr_vals) or 0
    atr_float = float(atr_val)
    sl = entry - config.sl_atr_mult * atr_float
    tp = entry + config.tp_atr_mult * atr_float
    min_sl_price = entry * (1 - config.min_sl_pct / 100)
    if sl > min_sl_price:
        sl = min_sl_price
    rsi_vals = rsi(candles, config.rsi_period)
    current_rsi = _last(rsi_vals)
    rsi_float = float(current_rsi) if current_rsi else 50.0
    atr_pct = atr_float / entry * 100 if entry > 0 else 0.0
    return ScalpSignal(
        should_trade=True, action="buy",
        entry_price=entry, take_profit=tp, stop_loss=sl,
        reason=f"watchlist_confirm (drop={drop_pct:.1f}%)",
        drop_pct=round(drop_pct, 2),
        rsi=round(rsi_float, 1),
        atr_pct=round(atr_pct, 2),
    )


def evaluate_entry_with_watchlist(symbol, candles, config, watchlist, now_ts):
    if not config.watchlist_enabled:
        return evaluate_entry(candles, config)
    if len(candles) < config.warmup_candles:
        return None

    if symbol in watchlist:
        entry = watchlist[symbol]
        detected_px = entry["detected_px"]
        current = float(candles[-1].close)
        if detected_px > 0:
            extra = (detected_px - current) / detected_px * 100.0
            if extra >= config.watchlist_extra_drop_pct:
                del watchlist[symbol]
                return None
        greens = _count_recent_greens(candles)
        if greens >= 2:
            drop_pct = _drop_pct_at(candles, len(candles) - 1, config.lookback_high)
            sig = _build_confirmation_signal(candles, config, drop_pct)
            del watchlist[symbol]
            return sig
        entry["candles_since"] += 1
        if entry["candles_since"] >= config.watchlist_max_candles:
            del watchlist[symbol]
        return None

    if _is_fresh_dip(candles, config):
        drop_pct = _drop_pct_at(candles, len(candles) - 1, config.lookback_high)
        watchlist[symbol] = {
            "detected_px": float(candles[-1].close),
            "detected_ts": now_ts,
            "detected_drop_pct": round(drop_pct, 2),
            "candles_since": 0,
        }
        return None

    return evaluate_entry(candles, config)


def is_uptrend_unfavorable(
    candles: list[Candle],
    config: ScalpMasterConfig,
) -> bool:
    """True if price is in strong uptrend (bad for dip-buying)."""
    if not config.trend_filter_enabled:
        return False
    if len(candles) < config.trend_ema_period + 5:
        return False
    ema_vals = ema(candles, config.trend_ema_period)
    ema_now = _last(ema_vals)
    if ema_now is None or float(ema_now) <= 0:
        return False
    price = float(candles[-1].close)
    gap_pct = (price - float(ema_now)) / float(ema_now) * 100.0
    lookback = min(10, len(ema_vals) - 1)
    if lookback <= 0:
        return False
    ema_prev = ema_vals[-(lookback + 1)]
    if ema_prev is None or float(ema_prev) <= 0:
        return False
    slope_pct = (float(ema_now) - float(ema_prev)) / float(ema_prev) * 100.0
    return gap_pct > config.trend_ema_gap_pct and slope_pct > 0


def evaluate_entry(
    candles: list[Candle],
    config: ScalpMasterConfig,
) -> ScalpSignal | None:
    """تصمیم ورود با تأیید برگشت."""
    if len(candles) < config.warmup_candles:
        return None

    if is_uptrend_unfavorable(candles, config):
        return None

    current = candles[-1]
    entry_price = float(current.close)

    # ---------- ۰. نقدشوندگی: کندل بدون معامله/flat معتبر نیست ----------
    if float(current.volume) <= 0 or current.high == current.low:
        return None

    # ---------- ۱. افت ----------
    lookback = candles[-config.lookback_high:]
    recent_high = max(float(c.high) for c in lookback)
    drop_pct = (recent_high - entry_price) / recent_high * 100

    if drop_pct < config.drop_threshold_pct:
        return None

    # ---------- ۲. تأیید برگشت: ۲ کندل سبز ----------
    if len(candles) < 3:
        return None

    prev = candles[-2]
    curr = candles[-1]

    prev_is_green = float(prev.close) > float(prev.open)
    curr_is_green = float(curr.close) > float(curr.open)
    curr_higher = float(curr.close) > float(prev.close)

    if not (prev_is_green and curr_is_green and curr_higher):
        return None

    # ---------- ۳. RSI ----------
    rsi_vals = rsi(candles, config.rsi_period)
    current_rsi = _last(rsi_vals)
    rsi_float = float(current_rsi) if current_rsi else 50.0

    if rsi_float < config.rsi_min or rsi_float > config.rsi_max:
        return None

    # ---------- ۴. کیفیت کندل ----------
    hl_range = float(curr.high) - float(curr.low)
    if hl_range <= 0:
        return None

    body = abs(float(curr.close) - float(curr.open))
    body_ratio = body / hl_range

    if body_ratio < config.min_body_ratio:
        return None

    # ---------- ۵. ATR ----------
    atr_vals = atr(candles, 14)
    atr_val = _last(atr_vals)
    if atr_val is None or atr_val <= 0:
        return None

    atr_float = float(atr_val)
    atr_pct = atr_float / entry_price * 100

    # ---------- ۶. فیلتر سقوط آزاد ----------
    ema20_vals = ema(candles, 20)
    ema20 = _last(ema20_vals)
    if ema20:
        dist = (float(ema20) - entry_price) / float(ema20) * 100
        if dist > config.max_dist_from_ema:
            return None

    # ---------- ۷. SL/TP پویا ----------
    sl = entry_price - config.sl_atr_mult * atr_float
    tp = entry_price + config.tp_atr_mult * atr_float

    # محافظت: SL حداقل
    min_sl_pct = config.min_sl_pct
    max_sl_price = entry_price * (1 - min_sl_pct / 100)
    if sl > max_sl_price:
        sl = max_sl_price

    return ScalpSignal(
        should_trade=True,
        action="buy",
        entry_price=entry_price,
        take_profit=tp,
        stop_loss=sl,
        reason=f"افت {drop_pct:.1f}% | ۲ کندل سبز | RSI={rsi_float:.0f} | ATR={atr_pct:.2f}%",
        drop_pct=round(drop_pct, 2),
        rsi=round(rsi_float, 1),
        atr_pct=round(atr_pct, 2),
    )


def evaluate_exit(
    candles: list[Candle],
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    candles_in_position: int,
    config: ScalpMasterConfig,
) -> tuple[bool, float, str]:
    """تصمیم خروج."""
    if not candles:
        return False, 0, ""

    current = candles[-1]
    high = float(current.high)
    low = float(current.low)
    close = float(current.close)

    # SL
    if low <= stop_loss:
        return True, stop_loss, "stop_loss"

    # TP
    if high >= take_profit:
        return True, take_profit, "take_profit"

    # Timeout
    if candles_in_position >= config.timeout_candles:
        return True, close, "timeout"

    return False, 0, ""


def diagnose_entry(candles: list[Candle], config: ScalpMasterConfig) -> list[dict]:
    """نتیجه‌ی تک‌تک شرط‌های ورود (برای فید «مغز ربات»). evaluate_entry را تغییر نمی‌دهد."""
    checks: list[dict] = []

    def add(name, label, passed, value, threshold):
        checks.append({
            "name": name, "label": label, "passed": bool(passed),
            "value": value, "threshold": threshold,
        })

    if len(candles) < config.warmup_candles:
        add("warmup", "داده کافی", False, len(candles), config.warmup_candles)
        return checks

    curr = candles[-1]
    prev = candles[-2]
    price = float(curr.close)

    add("liquidity", "نقدشوندگی", float(curr.volume) > 0 and curr.high != curr.low,
        float(curr.volume), None)

    lookback = candles[-config.lookback_high:]
    high = max(float(c.high) for c in lookback)
    drop = (high - price) / high * 100 if high > 0 else 0.0
    add("drop", "افت", drop >= config.drop_threshold_pct, round(drop, 2), config.drop_threshold_pct)

    green = (
        float(prev.close) > float(prev.open)
        and float(curr.close) > float(curr.open)
        and float(curr.close) > float(prev.close)
    )
    add("green", "۲ کندل سبز", green, None, None)

    r = _last(rsi(candles, config.rsi_period))
    r = float(r) if r else 50.0
    add("rsi", "RSI", config.rsi_min <= r <= config.rsi_max, round(r, 1),
        f"{config.rsi_min:.0f}-{config.rsi_max:.0f}")

    rng = float(curr.high) - float(curr.low)
    body = abs(float(curr.close) - float(curr.open)) / rng if rng > 0 else 0.0
    add("body", "بدنه کندل", body >= config.min_body_ratio, round(body, 2), config.min_body_ratio)

    a = _last(atr(candles, 14))
    a_pct = float(a) / price * 100 if (a and price > 0) else 0.0
    add("atr", "ATR", bool(a and a > 0), round(a_pct, 2), None)

    e = _last(ema(candles, 20))
    dist = (float(e) - price) / float(e) * 100 if e else 0.0
    add("ema", "فاصله از EMA", dist <= config.max_dist_from_ema, round(dist, 2), config.max_dist_from_ema)

    return checks


def evaluate_entry_range(candles: list[Candle], config: ScalpMasterConfig) -> ScalpSignal | None:
    """Range-mode entry: only in ADX<max + RSI<max + volume spike + green body."""
    if len(candles) < config.warmup_candles:
        return None

    # Gate 1: ADX < threshold (range market, not trending)
    adx_now = _last(adx(candles, 14))
    if adx_now is None or float(adx_now) >= config.range_adx_max:
        return None

    # Gate 2: RSI < threshold (oversold)
    rsi_now = _last(rsi(candles, config.rsi_period))
    if rsi_now is None or float(rsi_now) >= config.range_rsi_max:
        return None

    # Gate 3: Volume spike >= mult × avg
    vol_avg = _last(volume_sma(candles, 20))
    if vol_avg is None or float(vol_avg) <= 0:
        return None
    if float(candles[-1].volume) < config.range_volume_mult * float(vol_avg):
        return None

    # Gate 4: green candle with body >= threshold
    curr = candles[-1]
    o = float(curr.open)
    c = float(curr.close)
    if c <= o or o <= 0:
        return None
    body_pct = (c - o) / o * 100.0
    if body_pct < config.range_green_body_pct:
        return None

    # Build signal with ATR-based SL/TP (R/R = tp_mult/sl_mult = 2:1)
    atr_now = _last(atr(candles, 14))
    if atr_now is None or float(atr_now) <= 0:
        return None
    atr_float = float(atr_now)
    entry_price = c
    sl = entry_price - config.sl_atr_mult * atr_float
    tp = entry_price + config.tp_atr_mult * atr_float
    min_sl_price = entry_price * (1 - config.min_sl_pct / 100)
    if sl > min_sl_price:
        sl = min_sl_price

    rsi_float = float(rsi_now)
    atr_pct = atr_float / entry_price * 100 if entry_price > 0 else 0.0
    return ScalpSignal(
        should_trade=True, action="buy",
        entry_price=entry_price, take_profit=tp, stop_loss=sl,
        reason=f"range_mode: ADX={float(adx_now):.1f} RSI={rsi_float:.0f} body={body_pct:.2f}%",
        drop_pct=0.0,
        rsi=round(rsi_float, 1),
        atr_pct=round(atr_pct, 2),
    )
