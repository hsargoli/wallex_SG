"""Grid Bot — استراتژی گرید با دید کف‌شناسی.

منطق:
  ۱. N سطح خرید بر اساس ATR
  ۲. Bottom Detector تعیین می‌کنه که از کجا شروع کنیم
  ۳. وقتی میانگین قیمت بالای TP رفت → خروج همه
  ۴. اگه قیمت از حد پایین گرید گذشت → SL همه
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bottom_detector import detect_bottom
from app.services.indicators import atr, ema

# ---------- تنظیمات ----------
GRID_LEVELS = 3  # تعداد سطح
LEVEL_SPACING_ATR = 1.0  # فاصله بین سطوح = 1× ATR
TP_ABOVE_AVG_ATR = 1.5  # TP = میانگین + 1.5× ATR
HARD_SL_ATR = 4.0  # SL اضطراری = ورود اول - 4× ATR
CAPITAL_PER_LEVEL_PCT = 33.0  # هر سطح 33% سرمایه

# Bottom detection adjustments
BOTTOM_SCORE_AGGRESSIVE = 5  # score >= 5 → شروع از بالا
BOTTOM_SCORE_CONSERVATIVE = 3  # score < 3 → محافظه‌کار


@dataclass(slots=True)
class GridPlan:
    """پلن گرید برای یک نماد."""

    should_start: bool
    symbol: str
    levels: list[float]  # قیمت سطوح
    quantity_per_level: float  # مقدار در هر سطح
    take_profit: float  # قیمت TP روی میانگین
    hard_stop_loss: float  # SL اضطراری
    reason: str
    bottom_score: int
    atr_pct: float


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def plan_grid(
    candles: list[Candle],
    symbol: str,
    available_capital: float,
) -> GridPlan | None:
    """
    برنامه‌ریزی گرید برای یک نماد.
    """
    if len(candles) < 50:
        return None

    current = candles[-1]
    entry_price = float(current.close)

    # ---------- ۱. ATR برای spacing ----------
    atr14_vals = atr(candles, 14)
    current_atr = _last(atr14_vals)
    if current_atr is None or current_atr <= 0:
        return None

    atr_float = float(current_atr)
    atr_pct = atr_float / entry_price * 100

    # ---------- ۲. Bottom Score ----------
    bottom = detect_bottom(candles)
    bottom_score = bottom.score

    # ---------- ۳. تعیین شروع گرید ----------
    # اگه bottom قوی: شروع از قیمت فعلی
    # اگه bottom ضعیف: شروع از پایین‌تر (منتظر افت)
    if bottom_score >= BOTTOM_SCORE_AGGRESSIVE:
        # تهاجمی: از قیمت فعلی
        start_offset_atr = 0.0
        style = "aggressive"
    elif bottom_score >= BOTTOM_SCORE_CONSERVATIVE:
        # متوسط: کمی پایین‌تر
        start_offset_atr = 0.5
        style = "moderate"
    else:
        # محافظه‌کار: بذار بیشتر افت کنه
        start_offset_atr = 1.5
        style = "conservative"

    # ---------- ۴. چک روند (فیلتر سخت) ----------
    ema20_vals = ema(candles, 20)
    ema50_vals = ema(candles, 50)
    ema20 = _last(ema20_vals)
    ema50 = _last(ema50_vals)

    if ema20 is not None and ema50 is not None:
        # اگه روند خیلی نزولیه، شروع نکن
        if float(ema20) < float(ema50) * 0.98:
            return GridPlan(
                should_start=False,
                symbol=symbol,
                levels=[],
                quantity_per_level=0,
                take_profit=0,
                hard_stop_loss=0,
                reason="روند نزولی قوی",
                bottom_score=bottom_score,
                atr_pct=round(atr_pct, 2),
            )

    # ---------- ۵. ساخت سطوح ----------
    levels = []
    for i in range(GRID_LEVELS):
        offset = (start_offset_atr + i * LEVEL_SPACING_ATR) * atr_float
        level_price = entry_price - offset
        if level_price <= 0:
            break
        levels.append(round(level_price, 8))

    if len(levels) < 2:
        return None

    # ---------- ۶. TP و SL ----------
    avg_price = sum(levels) / len(levels)
    take_profit = avg_price + TP_ABOVE_AVG_ATR * atr_float
    hard_sl = levels[-1] - (HARD_SL_ATR - LEVEL_SPACING_ATR * (GRID_LEVELS - 1)) * atr_float
    if hard_sl <= 0:
        hard_sl = levels[-1] * 0.95

    # ---------- ۷. مقدار هر سطح ----------
    capital_per_level = available_capital * (CAPITAL_PER_LEVEL_PCT / 100)
    quantity_per_level = capital_per_level / avg_price

    return GridPlan(
        should_start=True,
        symbol=symbol,
        levels=levels,
        quantity_per_level=quantity_per_level,
        take_profit=round(take_profit, 8),
        hard_stop_loss=round(hard_sl, 8),
        reason=f"{style} (score={bottom_score}, ATR={atr_pct:.2f}%)",
        bottom_score=bottom_score,
        atr_pct=round(atr_pct, 2),
    )


# ============ Live Grid State ============


@dataclass
class GridPosition:
    """وضعیت فعلی گرید."""

    symbol: str
    levels: list[float]
    filled_levels: list[float]  # سطوحی که پر شدن
    quantities: list[float]  # مقدار در هر سطح
    avg_price: float  # میانگین قیمت فعلی
    total_invested: float
    take_profit: float
    hard_stop_loss: float


def calculate_grid_state(plan: GridPlan, current_price: float) -> GridPosition:
    """محاسبه‌ی وضعیت فعلی گرید بر اساس قیمت."""
    filled_prices = []
    filled_qtys = []

    for level in plan.levels:
        if current_price <= level:
            filled_prices.append(level)
            filled_qtys.append(plan.quantity_per_level)

    if not filled_prices:
        avg = 0
        total_inv = 0
    else:
        total_qty = sum(filled_qtys)
        total_inv = sum(p * q for p, q in zip(filled_prices, filled_qtys))
        avg = total_inv / total_qty if total_qty > 0 else 0

    return GridPosition(
        symbol=plan.symbol,
        levels=plan.levels,
        filled_levels=filled_prices,
        quantities=filled_qtys,
        avg_price=avg,
        total_invested=total_inv,
        take_profit=plan.take_profit,
        hard_stop_loss=plan.hard_stop_loss,
    )
