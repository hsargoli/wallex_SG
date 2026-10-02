"""Grid Improved — با ۴ بهبود کلیدی."""

import asyncio
from dataclasses import dataclass

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr, ema, sma

SYMBOLS = ["DOGETMN", "XRPTMN", "TRXTMN", "ADATMN", "GRAMTMN", "ZECTMN", "LINKTMN", "HBARTMN"]
TF = "1h"
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
N_LEVELS = 3


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TF, limit=2000)
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


@dataclass
class Config:
    cash_pct: float = 25.0
    spacing: float = 0.6
    escape_pct: float = 5.0
    timeout: int = 100
    adx_max: float = 25.0
    # New improvements
    max_exposure_pct: float = 40.0
    session_loss_limit_pct: float = 2.0
    use_ema_neutral_filter: bool = True
    use_bb_width_filter: bool = True


def backtest_symbol(symbol, candles, initial_cash, cfg: Config):
    cash = initial_cash
    holdings = 0.0
    avg_buy = 0.0
    trades = []
    peak = initial_cash
    max_dd = 0.0
    session = None
    sessions_skipped = 0

    for idx in range(100, len(candles)):
        price = float(candles[idx].close)
        window = candles[: idx + 1]

        equity = cash + holdings * price
        if equity > peak: peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        if dd > max_dd: max_dd = dd

        # ---------- شروع session جدید ----------
        if session is None:
            # ---------- Improvement 3: Trend Filter ----------
            adx = _calc_adx(window, 14)
            if adx >= cfg.adx_max:
                sessions_skipped += 1
                continue

            # EMA Neutral Filter: EMA50 ≈ EMA200 (نه روند)
            if cfg.use_ema_neutral_filter:
                ema50 = _last(ema(window, 50))
                ema200 = _last(ema(window, 200)) if len(window) >= 200 else None
                if ema50 and ema200:
                    diff_pct = abs(float(ema50) - float(ema200)) / float(ema200) * 100
                    if diff_pct > 3.0:  # بیش از 3% فاصله → روند داره
                        sessions_skipped += 1
                        continue

            # BB Width Filter (بازار جمع شده)
            if cfg.use_bb_width_filter and len(window) >= 30:
                closes = [float(c.close) for c in window[-20:]]
                mean = sum(closes) / len(closes)
                variance = sum((c - mean) ** 2 for c in closes) / len(closes)
                std = variance ** 0.5
                bb_width_pct = (2 * std / mean) * 100
                if bb_width_pct > 3.0:  # بازار پرنوسان
                    sessions_skipped += 1
                    continue

            atr_vals = atr(window, 14)
            atr_v = _last(atr_vals)
            if atr_v is None or atr_v <= 0:
                continue
            spacing = float(atr_v) * cfg.spacing
            if spacing <= 0 or spacing > price * 0.1:
                continue

            cap_per = cash * (cfg.cash_pct / 100)
            levels = []
            for i in range(1, N_LEVELS + 1):
                bp = price - i * spacing
                if bp <= 0: continue
                levels.append({
                    "buy_price": bp,
                    "sell_price": bp + spacing,
                    "qty": cap_per / bp,
                    "state": "waiting",
                })
            if len(levels) < N_LEVELS: continue

            session = {
                "levels": levels,
                "start_price": price,
                "start_idx": idx,
                "spacing": spacing,
            }
            continue

        # ---------- Improvement 2: Session Loss Limit ----------
        session_equity = cash + holdings * price
        session_loss_pct = (session_equity - (cash + holdings * session["start_price"])) / (cash + holdings * session["start_price"]) * 100
        if session_loss_pct < -cfg.session_loss_limit_pct:
            # بستن اجباری
            if holdings > 0:
                rev = holdings * price
                fee = rev * FEE_PCT / 100
                cash += rev - fee
                trades.append((rev - fee) - holdings * avg_buy)
                holdings = 0
                avg_buy = 0
            session = None
            continue

        # ---------- Escape ----------
        if abs(price - session["start_price"]) / session["start_price"] * 100 > cfg.escape_pct:
            if holdings > 0:
                rev = holdings * price
                fee = rev * FEE_PCT / 100
                cash += rev - fee
                trades.append((rev - fee) - holdings * avg_buy)
                holdings = 0
                avg_buy = 0
            session = None
            continue

        # ---------- Timeout ----------
        if idx - session["start_idx"] > cfg.timeout:
            if holdings > 0:
                rev = holdings * price
                fee = rev * FEE_PCT / 100
                cash += rev - fee
                trades.append((rev - fee) - holdings * avg_buy)
                holdings = 0
                avg_buy = 0
            session = None
            continue

        # ---------- Improvement 1: Max Exposure ----------
        current_exposure_pct = (holdings * price) / equity * 100 if equity > 0 else 0
        can_buy = current_exposure_pct < cfg.max_exposure_pct

        for lvl in session["levels"]:
            if lvl["state"] == "waiting" and price <= lvl["buy_price"]:
                if not can_buy:
                    continue
                cost = lvl["qty"] * price
                fee = cost * FEE_PCT / 100
                if cost + fee <= cash:
                    cash -= cost + fee
                    if holdings > 0:
                        old = avg_buy * holdings
                        holdings += lvl["qty"]
                        avg_buy = (old + cost) / holdings
                    else:
                        holdings = lvl["qty"]
                        avg_buy = price
                    lvl["state"] = "holding"
                    # آپدیت can_buy
                    equity = cash + holdings * price
                    current_exposure_pct = (holdings * price) / equity * 100 if equity > 0 else 0
                    can_buy = current_exposure_pct < cfg.max_exposure_pct

            elif lvl["state"] == "holding" and price >= lvl["sell_price"]:
                qty = min(lvl["qty"], holdings)
                if qty <= 0: continue
                rev = qty * price
                fee = rev * FEE_PCT / 100
                cash += rev - fee
                trades.append((rev - fee) - qty * avg_buy)
                holdings -= qty
                if holdings <= 1e-12:
                    holdings = 0
                    avg_buy = 0
                lvl["state"] = "waiting"

    if holdings > 0:
        price = float(candles[-1].close)
        rev = holdings * price
        fee = rev * FEE_PCT / 100
        cash += rev - fee
        trades.append((rev - fee) - holdings * avg_buy)

    return {
        "initial": initial_cash,
        "final": cash,
        "trades": trades,
        "max_dd": max_dd,
        "sessions_skipped": sessions_skipped,
    }


async def main():
    data = await fetch_all()
    print(f"✅ {len(data)} نماد\n")

    configs = [
        ("Baseline (بدون بهببود)", Config(
            use_ema_neutral_filter=False,
            use_bb_width_filter=False,
            max_exposure_pct=100.0,
            session_loss_limit_pct=100.0,
        )),
        ("+ Max Exposure 40%", Config(
            use_ema_neutral_filter=False,
            use_bb_width_filter=False,
            max_exposure_pct=40.0,
            session_loss_limit_pct=100.0,
        )),
        ("+ Session Loss 2%", Config(
            use_ema_neutral_filter=False,
            use_bb_width_filter=False,
            max_exposure_pct=100.0,
            session_loss_limit_pct=2.0,
        )),
        ("+ EMA Neutral Filter", Config(
            use_ema_neutral_filter=True,
            use_bb_width_filter=False,
            max_exposure_pct=100.0,
            session_loss_limit_pct=100.0,
        )),
        ("+ همه‌ی improvements", Config(
            use_ema_neutral_filter=True,
            use_bb_width_filter=True,
            max_exposure_pct=40.0,
            session_loss_limit_pct=2.0,
        )),
    ]

    n = len(data)
    per = INITIAL_CAPITAL / n

    print(f"{'config':<30} {'بازده':>10} {'ترید':>6} {'WR':>6} {'DD':>7} {'R/DD':>6} {'skip':>5}")
    print("─" * 80)

    for name, cfg in configs:
        all_trades = []
        total_final = 0
        worst_dd = 0
        total_skip = 0

        for sym, candles in data.items():
            r = backtest_symbol(sym, candles, per, cfg)
            total_final += r["final"]
            all_trades.extend(r["trades"])
            worst_dd = max(worst_dd, r["max_dd"])
            total_skip += r["sessions_skipped"]

        wins = sum(1 for t in all_trades if t > 0)
        wr = wins / len(all_trades) * 100 if all_trades else 0
        ret = (total_final / INITIAL_CAPITAL - 1) * 100
        rdd = ret / worst_dd if worst_dd > 0 else 0

        print(f"{name:<30} {ret:>+9.2f}% {len(all_trades):>6} {wr:>5.1f}% {worst_dd:>6.2f}% {rdd:>6.2f} {total_skip:>5}")


if __name__ == "__main__":
    asyncio.run(main())
