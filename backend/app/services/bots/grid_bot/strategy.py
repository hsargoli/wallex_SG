"""Grid Bot Strategy — پله‌ای خرید/فروش.

منطق:
  ۱. در بازار رنج (ADX پایین) فعال می‌شه
  ۲. N سطح خرید زیر قیمت فعلی
  ۳. N سطح فروش بالای قیمت فعلی
  ۴. هر سطح پر شد → سود کوچیک در سطح بعدی
"""

from dataclasses import dataclass, field

from app.domain.entities.candle import Candle
from app.services.bots.grid_bot.config import GridBotConfig
from app.services.indicators import atr


@dataclass
class GridLevel:
    price: float
    level_type: str  # "buy" | "sell"
    filled: bool = False
    fill_price: float = 0.0
    quantity: float = 0.0


@dataclass
class GridPlan:
    symbol: str
    center_price: float
    levels: list[GridLevel] = field(default_factory=list)
    total_invested: float = 0.0
    total_quantity: float = 0.0
    avg_price: float = 0.0
    real_revenue: float = 0.0
    realized_pnl: float = 0.0
    created_at: int = 0


@dataclass
class GridSignal:
    should_start: bool
    plan: GridPlan | None
    reason: str
    adx: float
    is_ranging: bool


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def _calc_adx(candles: list[Candle], period: int = 14) -> float:
    """محاسبه ADX (کپی از trend_follow)."""
    if len(candles) < period + 2:
        return 100.0  # اگه داده کافی نیست، فرض کن trending

    trs, plus_dm, minus_dm = [], [], []
    for i in range(1, len(candles)):
        h = float(candles[i].high)
        l = float(candles[i].low)
        ph = float(candles[i - 1].high)
        pl = float(candles[i - 1].low)
        pc = float(candles[i - 1].close)
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
        up = h - ph
        dn = pl - l
        plus_dm.append(up if up > dn and up > 0 else 0)
        minus_dm.append(dn if dn > up and dn > 0 else 0)

    if len(trs) < period:
        return 100.0

    atr_v = sum(trs[:period]) / period
    p_avg = sum(plus_dm[:period]) / period
    m_avg = sum(minus_dm[:period]) / period

    dx_vals = []
    for i in range(period, len(trs)):
        atr_v = (atr_v * (period - 1) + trs[i]) / period
        p_avg = (p_avg * (period - 1) + plus_dm[i]) / period
        m_avg = (m_avg * (period - 1) + minus_dm[i]) / period
        if atr_v == 0:
            continue
        pdi = 100 * p_avg / atr_v
        mdi = 100 * m_avg / atr_v
        s = pdi + mdi
        if s > 0:
            dx_vals.append(100 * abs(pdi - mdi) / s)

    if not dx_vals:
        return 100.0
    return sum(dx_vals[-period:]) / min(period, len(dx_vals))


def should_start_grid(
    candles: list[Candle],
    symbol: str,
    available_capital: float,
    config: GridBotConfig,
) -> GridSignal:
    """بررسی آیا باید گرید جدید بسازیم."""
    if len(candles) < config.warmup_candles:
        return GridSignal(False, None, "داده کم", 0, False)

    # ---------- فیلتر رنج ----------
    adx = _calc_adx(candles, 14)
    is_ranging = adx < config.adx_max

    if config.use_range_filter and not is_ranging:
        return GridSignal(
            False,
            None,
            f"بازار trending است (ADX={adx:.0f} > {config.adx_max})",
            adx,
            False,
        )

    # ---------- ATR برای spacing ----------
    atr_vals = atr(candles, 14)
    current_atr = _last(atr_vals)
    if current_atr is None or current_atr <= 0:
        return GridSignal(False, None, "ATR نامشخص", adx, is_ranging)

    atr_f = float(current_atr)
    center = float(candles[-1].close)
    spacing = config.grid_spacing_atr * atr_f

    if spacing <= 0:
        return GridSignal(False, None, "spacing صفر", adx, is_ranging)

    # ---------- ساخت سطوح ----------
    capital_per_level = available_capital * (config.cash_per_level_pct / 100)

    plan = GridPlan(
        symbol=symbol,
        center_price=center,
        created_at=candles[-1].time,
    )

    # سطوح خرید (زیر قیمت)
    for i in range(1, config.n_buy_levels + 1):
        price = center - (i * spacing)
        if price <= 0:
            continue
        level = GridLevel(
            price=price,
            level_type="buy",
            quantity=capital_per_level / price if price > 0 else 0,
        )
        plan.levels.append(level)

    # سطوح فروش (بالای قیمت)
    for i in range(1, config.n_sell_levels + 1):
        price = center + (i * spacing)
        level = GridLevel(
            price=price,
            level_type="sell",
            quantity=0,  # در ابتدا چیزی برای فروش نداریم
        )
        plan.levels.append(level)

    return GridSignal(
        True,
        plan,
        f"Grid در ADX={adx:.0f} | {len(plan.levels)} سطح",
        adx,
        True,
    )


def update_grid(
    plan: GridPlan,
    current_price: float,
    config: GridBotConfig,
) -> dict:
    """
    آپدیت گرید بر اساس قیمت فعلی.
    Returns: dict با fill ها و سود/زیان
    """
    fills = []
    realized = 0.0

    # ---------- بررسی fills ----------
    for level in plan.levels:
        if level.filled:
            # اگه sell level و قیمت بهش رسیده → بفروش
            if level.level_type == "sell" and current_price >= level.price:
                # فقط اگه موجودی داریم
                if plan.total_quantity > 0:
                    sell_qty = min(level.quantity or plan.total_quantity, plan.total_quantity)
                    if sell_qty > 0:
                        revenue = sell_qty * level.price
                        cost_basis = sell_qty * plan.avg_price
                        pnl = revenue - cost_basis
                        realized += pnl
                        plan.total_quantity -= sell_qty
                        plan.real_revenue += revenue
                        plan.realized_pnl += pnl
                        level.filled = False  # ریست برای دور بعد
                        fills.append(
                            {
                                "type": "sell",
                                "price": level.price,
                                "qty": sell_qty,
                                "pnl": pnl,
                            }
                        )
            continue

        # اگه buy level و قیمت بهش رسیده → بخر
        if level.level_type == "buy" and current_price <= level.price:
            level.filled = True
            level.fill_price = current_price
            level.quantity = level.quantity or 0
            cost = level.quantity * current_price
            plan.total_invested += cost
            # محاسبه‌ی میانگین
            if plan.total_quantity + level.quantity > 0:
                total_cost = plan.avg_price * plan.total_quantity + cost
                plan.total_quantity += level.quantity
                plan.avg_price = total_cost / plan.total_quantity if plan.total_quantity > 0 else 0
            fills.append(
                {
                    "type": "buy",
                    "price": current_price,
                    "qty": level.quantity,
                    "cost": cost,
                }
            )

    return {
        "fills": fills,
        "realized_pnl": realized,
        "total_invested": plan.total_invested,
        "total_quantity": plan.total_quantity,
        "avg_price": plan.avg_price,
    }


def should_reset_grid(
    plan: GridPlan,
    current_time: int,
    config: GridBotConfig,
) -> tuple[bool, str]:
    """آیا گرید باید ریست بشه؟"""
    hours_elapsed = (current_time - plan.created_at) / 3600
    if hours_elapsed >= config.reset_after_hours:
        return True, f"ریست بعد از {hours_elapsed:.0f} ساعت"
    return False, ""
