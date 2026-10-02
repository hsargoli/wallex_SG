"""Grid Backtest — نسخه تمیز با حساب‌داری درست.

اصول:
  ۱. cash: پول نقد
  ۲. holdings: مقدار دارایی
  ۳. avg_buy: میانگین قیمت خرید
  ۴. equity = cash + holdings × current_price
  ۵. هر خرید: cash کم، holdings زیاد
  ۶. هر فروش: cash زیاد، holdings کم
"""

import asyncio
from dataclasses import dataclass, field

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN", "BNBTMN",
           "ADATMN", "LINKTMN", "HBARTMN", "DASHTMN", "TRXTMN"]
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2


@dataclass
class GridState:
    """وضعیت فعلی گرید."""
    cash: float                        # پول نقد
    holdings: float = 0.0              # مقدار دارایی
    avg_buy: float = 0.0               # میانگین خرید

    @property
    def equity(self) -> float:
        """ارزش کل (نقد + دارایی)."""
        return self.cash  # holdings value باید جدا محاسبه بشه

    def buy(self, qty: float, price: float) -> bool:
        """خرید. اگر پول کافی نیست False."""
        cost = qty * price
        fee = cost * (FEE_PCT / 100)
        total = cost + fee
        if total > self.cash:
            return False
        # آپدیت میانگین
        if self.holdings > 0:
            old_cost = self.avg_buy * self.holdings
            self.holdings += qty
            self.avg_buy = (old_cost + cost) / self.holdings
        else:
            self.holdings = qty
            self.avg_buy = price
        self.cash -= total
        return True

    def sell(self, qty: float, price: float) -> float:
        """فروش. برمی‌گردونه PnL خالص."""
        if qty > self.holdings:
            qty = self.holdings
        revenue = qty * price
        fee = revenue * (FEE_PCT / 100)
        net = revenue - fee
        cost_basis = qty * self.avg_buy
        pnl = net - cost_basis
        self.holdings -= qty
        self.cash += net
        if self.holdings <= 0.000001:
            self.holdings = 0
            self.avg_buy = 0
        return pnl


@dataclass
class Stats:
    return_pct: float = 0.0
    trades: int = 0
    wins: int = 0
    losses: int = 0
    wr: float = 0.0
    max_dd: float = 0.0
    capital: float = 0.0
    sessions: int = 0
    escapes: int = 0


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


def run_backtest(markets_data, adx_max=25.0, spacing_mult=1.0,
                 n_levels=3, cash_per_level_pct=15.0,
                 target_pct=1.0, escape_pct=5.0, max_duration=100):

    state = GridState(cash=INITIAL_CAPITAL)
    all_pnls = []
    peak_equity = INITIAL_CAPITAL
    max_dd = 0.0

    for symbol, candles in markets_data.items():
        # سطوح گرید
        buy_levels: list[float] = []
        session_active = False
        session_start_idx = 0
        session_start_price = 0.0
        spacing = 0.0

        for idx in range(50, len(candles)):
            candle = candles[idx]
            price = float(candle.close)
            window = candles[: idx + 1]

            # محاسبه‌ی equity
            equity = state.cash + state.holdings * price
            if equity > peak_equity:
                peak_equity = equity
            dd = (peak_equity - equity) / peak_equity * 100
            if dd > max_dd:
                max_dd = dd

            # ---------- شروع session جدید ----------
            if not session_active:
                adx = _calc_adx(window, 14)
                if adx >= adx_max:
                    continue

                atr_vals = atr(window, 14)
                atr_v = _last(atr_vals)
                if atr_v is None or atr_v <= 0:
                    continue

                spacing = float(atr_v) * spacing_mult
                if spacing <= 0:
                    continue

                # ساخت سطوح خرید
                capital_per_level = state.cash * (cash_per_level_pct / 100)
                buy_levels = []
                for i in range(1, n_levels + 1):
                    p = price - i * spacing
                    if p > 0:
                        qty = capital_per_level / p
                        buy_levels.append({"price": p, "qty": qty})

                session_active = True
                session_start_idx = idx
                session_start_price = price
                continue

            # ---------- Escape ----------
            diff_pct = abs(price - session_start_price) / session_start_price * 100
            if diff_pct > escape_pct:
                # فروش اجباری
                if state.holdings > 0:
                    pnl = state.sell(state.holdings, price)
                    all_pnls.append(pnl)
                session_active = False
                continue

            # ---------- Timeout ----------
            if idx - session_start_idx > max_duration:
                if state.holdings > 0:
                    pnl = state.sell(state.holdings, price)
                    all_pnls.append(pnl)
                session_active = False
                continue

            # ---------- خرید: پر کردن سطوح ----------
            for lvl in buy_levels:
                if lvl.get("filled"):
                    continue
                if price <= lvl["price"]:
                    if state.buy(lvl["qty"], price):
                        lvl["filled"] = True

            # ---------- فروش: TP ----------
            if state.holdings > 0 and state.avg_buy > 0:
                target = state.avg_buy * (1 + target_pct / 100)
                if price >= target:
                    qty = state.holdings * 0.5  # فروش نیمی
                    pnl = state.sell(qty, price)
                    all_pnls.append(pnl)
                    # ریست سطوحی که پایین‌تر از قیمت فعلی هستند
                    for lvl in buy_levels:
                        if lvl["price"] < price - spacing:
                            lvl["filled"] = False

    # بستن باز
    for symbol, candles in markets_data.items():
        if state.holdings > 0:
            last_price = float(candles[-1].close)
            pnl = state.sell(state.holdings, last_price)
            all_pnls.append(pnl)

    final_capital = state.cash

    wins = sum(1 for p in all_pnls if p > 0)
    losses = sum(1 for p in all_pnls if p <= 0)

    return Stats(
        return_pct=(final_capital / INITIAL_CAPITAL - 1) * 100,
        trades=len(all_pnls),
        wins=wins,
        losses=losses,
        wr=wins / len(all_pnls) * 100 if all_pnls else 0,
        max_dd=max_dd,
        capital=final_capital,
    )


async def main():
    for tf in ["15m", "1h", "4h"]:
        data = await fetch_all(tf)
        if len(data) < 3:
            print(f"\n❌ TF={tf}")
            continue
        print(f"\n{'='*70}")
        print(f"🎯 TF={tf}  ({len(data)} نماد)")
        print(f"{'='*70}")
        stats = run_backtest(data)
        print(f"  بازده:       {stats.return_pct:>+10.2f}%")
        print(f"  سرمایه:      {stats.capital:>11,.0f}")
        print(f"  Max DD:      {stats.max_dd:>10.2f}%")
        print(f"  ترید:        {stats.trades:>11}")
        print(f"  برد/باخت:    {stats.wins:>5} / {stats.losses}")
        print(f"  WR:          {stats.wr:>10.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
