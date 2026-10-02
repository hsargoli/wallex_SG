"""Grid Bot Backtest — نسخه کامل."""

import asyncio
from dataclasses import dataclass, field
from typing import Literal

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.config import GridBotConfig
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN", "BNBTMN", "ADATMN", "LINKTMN", "HBARTMN", "DASHTMN", "TRXTMN"]
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2


@dataclass
class GridLevel:
    price: float
    level_type: Literal["buy", "sell"]
    quantity: float
    filled: bool = False
    fill_price: float = 0.0


@dataclass
class GridSession:
    symbol: str
    center_price: float
    spacing: float
    levels: list[GridLevel] = field(default_factory=list)
    created_idx: int = 0
    total_invested: float = 0.0
    total_quantity: float = 0.0
    avg_price: float = 0.0
    cycles_completed: int = 0
    realized_pnl: float = 0.0
    available_cash: float = 0.0

    def fill_price(self, current_price: float) -> list[dict]:
        """چک کردن fill سطوح. Returns list of fills."""
        fills = []

        for level in self.levels:
            if level.level_type == "buy" and not level.filled:
                if current_price <= level.price:
                    level.filled = True
                    level.fill_price = current_price
                    cost = level.quantity * current_price
                    self.total_invested += cost

                    # آپدیت میانگین
                    if self.total_quantity + level.quantity > 0:
                        old_cost = self.avg_price * self.total_quantity
                        self.total_quantity += level.quantity
                        self.avg_price = (old_cost + cost) / self.total_quantity

                    fills.append({
                        "type": "buy",
                        "price": current_price,
                        "level_price": level.price,
                        "qty": level.quantity,
                    })

            elif level.level_type == "sell" and level.filled and self.total_quantity > 0:
                # فقط اگه سطح sell و قیمت به اونجا رسیده
                # نکته: level.filled برای sell یعنی "آماده" هست
                pass

        return fills

    def check_sell(self, current_price: float) -> dict | None:
        """بررسی فروش در سود."""
        if self.total_quantity <= 0:
            return None

        # هدف فروش: میانگین + یک spacing
        target = self.avg_price * 1.01  # 1% بالای میانگین

        if current_price >= target:
            # بفروش نیمی از موجودی
            sell_qty = self.total_quantity * 0.5
            revenue = sell_qty * current_price
            cost = sell_qty * self.avg_price
            pnl = revenue - cost

            self.realized_pnl += pnl
            self.total_quantity -= sell_qty
            self.available_cash += revenue  # ← این خط اضافه شد!
            self.cycles_completed += 1

            # Reset buy levels که زیر قیمت فعلی هستن
            for level in self.levels:
                if level.level_type == "buy" and level.price < current_price - self.spacing:
                    level.filled = False

            return {
                "type": "sell",
                "price": current_price,
                "qty": sell_qty,
                "pnl": pnl,
                "target": target,
            }

        return None


@dataclass
class GridStats:
    return_pct: float = 0.0
    trades: int = 0
    cycles: int = 0
    wins: int = 0
    losses: int = 0
    wr: float = 0.0
    max_dd: float = 0.0
    capital: float = 0.0
    sessions: int = 0
    avg_cycles_per_session: float = 0.0
    avg_pnl_per_cycle: float = 0.0
    escape_count: int = 0


async def fetch_all(tf: str):
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=tf, limit=2000)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def _last(v):
    for x in reversed(v):
        if x is not None:
            return x
    return None


def run_grid_backtest(markets_data, config: GridBotConfig) -> GridStats:
    """Backtest کامل Grid."""

    stats = GridStats()
    capital = INITIAL_CAPITAL
    peak = capital

    # اگر می‌خوایم چند نماد رو همزمان مدیریت کنیم
    # اینجا ساده‌تر: هر نماد جدا
    all_pnls = []

    for symbol, candles in markets_data.items():
        session: GridSession | None = None

        for idx in range(config.warmup_candles, len(candles)):
            candle = candles[idx]
            current_price = float(candle.close)
            window = candles[: idx + 1]

            # ---------- اگر session فعال نیست، شاید شروع کنیم ----------
            if session is None:
                # چک range
                adx = _calc_adx(window, 14)
                if adx >= config.adx_max:
                    continue

                atr_vals = atr(window, 14)
                current_atr = _last(atr_vals)
                if current_atr is None or current_atr <= 0:
                    continue

                atr_f = float(current_atr)
                spacing = config.grid_spacing_atr * atr_f
                if spacing <= 0:
                    continue

                # ساخت سطوح
                capital_per_level = capital * (config.capital_per_level_pct / 100)
                levels = []
                for i in range(1, config.n_buy_levels + 1):
                    p = current_price - i * spacing
                    if p > 0:
                        levels.append(GridLevel(price=p, level_type="buy", quantity=capital_per_level / p))

                session = GridSession(
                    symbol=symbol,
                    center_price=current_price,
                    spacing=spacing,
                    levels=levels,
                    created_idx=idx,
                    available_cash=capital,  # ← کل سرمایه در دسترس
                )
                stats.sessions += 1
                continue

            # ---------- آپدیت session فعال ----------
            # چک escape (خروج از range)
            price_diff_pct = abs(current_price - session.center_price) / session.center_price * 100
            if price_diff_pct > 3:  # 3% دور از مرکز → escape (سخت‌گیرانه‌تر)
                # بستن session
                if session.total_quantity > 0:
                    # فروش اجباری
                    revenue = session.total_quantity * current_price
                    cost = session.total_quantity * session.avg_price
                    pnl = revenue - cost
                    session.realized_pnl += pnl
                    all_pnls.append(pnl)
                    stats.trades += 1
                    if pnl > 0:
                        stats.wins += 1
                    else:
                        stats.losses += 1

                stats.escape_count += 1
                stats.cycles += session.cycles_completed

                # آپدیت capital
                capital += session.realized_pnl
                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100
                if dd > stats.max_dd:
                    stats.max_dd = dd

                session = None
                continue

            # Fill خرید
            fills = session.fill_price(current_price)
            for fill in fills:
                # اگه این خرید از موجودی خارج شده؟
                pass

            # چک فروش
            sell = session.check_sell(current_price)
            if sell:
                all_pnls.append(sell["pnl"])
                stats.trades += 1
                if sell["pnl"] > 0:
                    stats.wins += 1
                else:
                    stats.losses += 1

                # ✅ capital = نقد + هزینه‌ی دارایی باقیمانده
                capital = session.available_cash + (session.total_quantity * current_price)
                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100
                if dd > stats.max_dd:
                    stats.max_dd = dd

    stats.capital = capital
    stats.return_pct = (capital / INITIAL_CAPITAL - 1) * 100
    stats.wr = stats.wins / stats.trades * 100 if stats.trades else 0
    if stats.sessions > 0:
        stats.avg_cycles_per_session = stats.cycles / stats.sessions
    if all_pnls:
        stats.avg_pnl_per_cycle = sum(all_pnls) / len(all_pnls)

    return stats


def print_result(tf: str, stats: GridStats):
    print(f"\n{'='*70}")
    print(f"🎯 TF={tf}")
    print(f"{'='*70}")
    print(f"  بازده:          {stats.return_pct:>+10.2f}%")
    print(f"  سرمایه نهایی:    {stats.capital:>11,.0f}")
    print(f"  Max DD:         {stats.max_dd:>10.2f}%")
    print("  ─────────────────────────────────")
    print(f"  تعداد sessions:  {stats.sessions:>11}")
    print(f"  cycles کامل:     {stats.cycles:>11}")
    print(f"  escape شده:      {stats.escape_count:>11}")
    print(f"  تریدها:         {stats.trades:>11}")
    print(f"  WR:             {stats.wr:>10.1f}%")
    print(f"  میانگین cycle:   {stats.avg_pnl_per_cycle:>+10.1f}")
    if stats.sessions > 0:
        print(f"  میانگین cycle/session: {stats.avg_cycles_per_session:.1f}")


async def main():
    config = GridBotConfig()
    print("🎛️  Config:")
    print(f"   ADX max:           {config.adx_max}")
    print(f"   Grid spacing ATR:  {config.grid_spacing_atr}")
    print(f"   Buy levels:        {config.n_buy_levels}")
    print(f"   Capital/level:     {config.capital_per_level_pct}%")

    for tf in ["15m", "1h", "4h"]:
        markets_data = await fetch_all(tf)
        if len(markets_data) < 3:
            print(f"\n❌ TF={tf}: داده کم")
            continue
        stats = run_grid_backtest(markets_data, config)
        print_result(tf, stats)


if __name__ == "__main__":
    asyncio.run(main())
