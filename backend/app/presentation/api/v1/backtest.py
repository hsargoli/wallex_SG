from datetime import datetime, timedelta
"""Backtest endpoint."""

from fastapi import APIRouter, HTTPException, status, Query

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.backtest import run_backtest
from app.infrastructure.exchange.historical_adapter import HistoricalExchangeAdapter

router = APIRouter(prefix="/backtest", tags=["Backtest"])


@router.get("/run/{symbol}")
async def run(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 1000,
    min_confidence: int = 50,
    max_duration: int = 24,
):
    """اجرای backtest روی یک نماد."""
    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles or len(candles) < 150:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="داده کافی نیست (حداقل ۱۵۰ کندل لازم است)",
        )

    result = run_backtest(
        candles=candles,
        symbol=symbol,
        timeframe=tf,
        min_confidence=min_confidence,
        max_duration=max_duration,
    )

    recent_trades = [
        {
            "entry_time": t.entry_time,
            "exit_time": t.exit_time,
            "entry_price": str(t.entry_price),
            "exit_price": str(t.exit_price),
            "side": t.side,
            "return_pct": round(t.return_pct, 3),
            "duration_candles": t.duration_candles,
            "exit_reason": t.exit_reason,
            "confidence": t.confidence,
        }
        for t in result.trades[-20:]
    ]

    return {
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "candles_analyzed": result.candles_analyzed,
        "signals_generated": result.signals_generated,
        "stats": {
            "total_trades": result.total_trades,
            "wins": result.wins,
            "losses": result.losses,
            "win_rate": round(result.win_rate, 2),
            "avg_win_pct": round(result.avg_win_pct, 3),
            "avg_loss_pct": round(result.avg_loss_pct, 3),
            "total_return_pct": round(result.total_return_pct, 3),
            "profit_factor": round(result.profit_factor, 3),
            "max_drawdown_pct": round(result.max_drawdown_pct, 3),
            "sharpe_ratio": round(result.sharpe_ratio, 3),
            "avg_duration_candles": round(result.avg_duration_candles, 1),
        },
        "equity_curve": result.equity_curve,
        "recent_trades": recent_trades,
    }


@router.get("/bot/{bot_slug}/{symbol}")
async def run_bot(
    bot_slug: str,
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 1000,
    initial_capital: float = 1000.0,
    position_size_pct: float = 50.0,
    fee_pct: float = 0.2,
    start_date: str = Query(None),
    end_date: str = Query(None),
):
    if start_date and end_date:
        exchange = HistoricalExchangeAdapter(start_date, end_date)

    """بک‌تست یک ربات روی داده‌ی گذشته (فعلاً فقط scalp_master)."""
    if bot_slug != "scalp_master":
        raise HTTPException(status_code=400, detail="فعلاً فقط scalp_master پشتیبانی می‌شود")

    from app.infrastructure.backtest.bot_backtest import run_scalp_backtest

    try:
        candles = await GetCandlesUseCase(exchange=exchange).execute(
            symbol=symbol, timeframe=tf, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles or len(candles) < 100:
        raise HTTPException(status_code=400, detail="داده کافی نیست (حداقل ۱۰۰ کندل)")

    result = run_scalp_backtest(
        candles,
        initial_capital=initial_capital,
        position_size_pct=position_size_pct,
        fee_pct=fee_pct,
    )
    for t in result["trades"]:
        t["symbol"] = symbol
    result["symbol"] = symbol
    result["timeframe"] = tf
    result["bot_slug"] = bot_slug
    return result


FALLBACK_SYMBOLS = [
    "NEARTMN", "SANDTMN", "ORCATMN", "BTCTMN", "ETHTMN", "SOLTMN", "XRPTMN",
    "DOGETMN", "ADATMN", "TRXTMN", "LTCTMN", "LINKTMN", "AVAXTMN", "DOTTMN", "SHIBTMN",
]


async def _pick_symbols(exchange, n: int) -> tuple[list[str], str]:
    """۱۵ نماد TMN با بیشترین حجم؛ در صورت شکست، لیست ثابت."""
    try:
        markets = await exchange.get_markets()
        rows = []
        for m in markets:
            sym = getattr(m, "symbol", None)
            if not sym or not str(sym).endswith("TMN"):
                continue
            vol = 0.0
            for f in ("daily_quote_volume", "volume_24h", "quote_volume", "volume"):
                v = getattr(m, f, None)
                if v is not None:
                    try:
                        vol = float(v)
                        break
                    except (TypeError, ValueError):
                        pass
            rows.append((vol, str(sym)))
        if rows and any(v > 0 for v, _ in rows):
            rows.sort(reverse=True)
            return [sym for _, sym in rows[:n]], "markets_by_volume"
    except Exception:
        pass
    return FALLBACK_SYMBOLS[:n], "fallback_list"


async def _run_scalp_multi(
    bot_slug: str,
    exchange,
    symbols: str = "",
    top: int = 15,
    tf: str = "1h",
    limit: int = 3000,
    initial_capital: float = 1000.0,
    position_size_pct: float = 50.0,
    fee_pct: float = 0.2,
):
    """بک‌تست چندنمادی (سرمایه‌ی مستقل برای هر نماد)."""
    import asyncio

    if bot_slug != "scalp_master":
        raise HTTPException(status_code=400, detail="فعلاً فقط scalp_master پشتیبانی می‌شود")

    from app.infrastructure.backtest.bot_backtest import run_scalp_backtest

    if symbols.strip():
        syms = list(dict.fromkeys(x.strip().upper() for x in symbols.split(",") if x.strip()))
        source = "manual"
        if not 1 <= len(syms) <= 5:
            raise HTTPException(status_code=400, detail="تعداد نمادها باید بین ۱ تا ۵ باشد")
    else:
        syms, source = await _pick_symbols(exchange, max(1, min(top, 30)))

    sem = asyncio.Semaphore(4)

    async def one(sym: str) -> dict:
        async with sem:
            try:
                candles = await GetCandlesUseCase(exchange=exchange).execute(
                    symbol=sym, timeframe=tf, limit=limit
                )
                if not candles or len(candles) < 100:
                    return {"symbol": sym, "error": "داده کافی نیست"}
                r = await asyncio.to_thread(
                    run_scalp_backtest, candles,
                    initial_capital=initial_capital,
                    position_size_pct=position_size_pct,
                    fee_pct=fee_pct,
                )
                for t in r["trades"]:
                    t["symbol"] = sym
                r["symbol"] = sym
                r["flat_pct"] = round(sum(1 for c in candles if c.high == c.low) / len(candles) * 100, 1)
                return r
            except Exception as e:
                return {"symbol": sym, "error": f"{type(e).__name__}: {e}"}

    results = await asyncio.gather(*(one(x) for x in syms))
    ok = [r for r in results if "error" not in r]
    failed = [{"symbol": r["symbol"], "error": r["error"]} for r in results if "error" in r]

    all_trades = sorted(
        (t for r in ok for t in r["trades"]), key=lambda t: t["entry_time"]
    )
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] <= 0]
    gw = sum(t["pnl"] for t in wins)
    gl = abs(sum(t["pnl"] for t in losses))
    n = len(all_trades)

    per_symbol = [
        {
            "symbol": r["symbol"],
            "candles": r["candles_analyzed"],
            "trades": r["total_trades"],
            "win_rate": r["win_rate"],
            "pnl_pct": r["total_pnl_pct"],
            "profit_factor": r["profit_factor"],
            "max_drawdown_pct": r["max_drawdown_pct"],
            "flat_pct": r["flat_pct"],
            "weak_data": r["flat_pct"] > 20,
        }
        for r in ok
    ]
    per_symbol.sort(key=lambda x: x["pnl_pct"], reverse=True)

    return {
        "bot_slug": bot_slug,
        "timeframe": tf,
        "symbols_source": source,
        "symbols_requested": len(syms),
        "symbols_ok": len(ok),
        "failed": failed,
        "summary": {
            "total_trades": n,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
            "avg_trade_pct": round(sum(t["pnl_pct"] for t in all_trades) / n, 2) if n else 0.0,
            "avg_symbol_pnl_pct": round(sum(x["pnl_pct"] for x in per_symbol) / len(per_symbol), 2) if per_symbol else 0.0,
            "profit_factor": round(gw / gl, 2) if gl > 0 else None,
            "worst_symbol_dd_pct": max((x["max_drawdown_pct"] for x in per_symbol), default=0.0),
            "reliable": n >= 30,
        },
        "per_symbol": per_symbol,
        "trades": all_trades,
    }


SIM_BOTS = ["trend_follow", "volatility_hunter", "volatility_hunter_v2", "mean_revert"]
ALL_BOTS = ["scalp_master"] + SIM_BOTS


def _pair_trades(raw: list[dict], times: list[int]) -> list[dict]:
    """ردیف‌های تخت BUY/SELL → ترید کامل."""
    out, open_buy = [], None
    for r in raw:
        side = str(r.get("side", "")).upper()
        if side == "BUY":
            open_buy = r
        elif side == "SELL" and open_buy is not None:
            size = float(open_buy.get("size_usd") or 0)
            pnl = float(r.get("pnl") or 0)
            i0, i1 = int(open_buy.get("i", 0)), int(r.get("i", 0))
            tm = lambda i: times[i] if 0 <= i < len(times) else 0
            out.append({
                "entry_time": tm(i0), "exit_time": tm(i1),
                "entry_price": float(open_buy.get("price") or 0),
                "exit_price": float(r.get("price") or 0),
                "pnl": round(pnl, 4),
                "pnl_pct": round(pnl / size * 100, 2) if size > 0 else 0.0,
                "exit_reason": str(r.get("reason", "")),
                "duration_candles": max(0, i1 - i0),
            })
            open_buy = None
    return out


@router.get("/bot/{bot_slug}")
async def run_bot_any(
    bot_slug: str,
    exchange: ExchangeDep,
    symbols: str = "",
    top: int = 15,
    tf: str = "1h",
    limit: int = 3000,
    initial_capital: float = 1000.0,
    position_size_pct: float = 50.0,
    fee_pct: float = 0.2,
    days: int = 30,
):
    """بک‌تست هر ربات (scalp_master: موتور خودمان؛ بقیه: Adapterها)."""
    if bot_slug not in ALL_BOTS:
        raise HTTPException(
            status_code=400,
            detail=f"ربات پشتیبانی نمی‌شود. مجاز: {', '.join(ALL_BOTS)}",
        )
    if bot_slug == "scalp_master":
        return await _run_scalp_multi(
            bot_slug, exchange, symbols=symbols, top=top, tf=tf, limit=limit,
            initial_capital=initial_capital, position_size_pct=position_size_pct, fee_pct=fee_pct,
        )

    import asyncio
    import datetime as dt

    from app.infrastructure.wallex_repo import WallexMarketData  # noqa: F401
    from app.services.bot_simulator import BotSimulator

    syms = list(dict.fromkeys(x.strip().upper() for x in symbols.split(",") if x.strip()))
    if not 1 <= len(syms) <= 5:
        raise HTTPException(status_code=400, detail="برای این ربات ۱ تا ۵ نماد لازم است")

    end = dt.date.today()
    start = end - dt.timedelta(days=max(7, min(days, 90)))
    sem = asyncio.Semaphore(3)

    async def one(sym: str) -> dict:
        async with sem:
            try:
                times = [
                    int(c.time) for c in await GetCandlesUseCase(exchange=exchange).execute(
                        symbol=sym, timeframe=tf, limit=limit)
                ]
                sim = BotSimulator(WallexMarketData(), bot_slug, initial_balance=initial_capital)
                res = await sim.run(start.isoformat(), end.isoformat(), sym, tf)
                if res.get("status") != "success":
                    return {"symbol": sym, "error": str(res.get("message") or res.get("status"))}
                # اندیس i به کندل‌های بازه‌ی شبیه‌ساز اشاره دارد؛ زمان‌ها را از انتهای لیست هم‌تراز می‌کنیم
                n_prices = int(res.get("prices_count") or len(times))
                aligned = times[-n_prices:] if n_prices <= len(times) else times
                trades = _pair_trades(res.get("trades", []), aligned)
                for t in trades:
                    t["symbol"] = sym
                return {"symbol": sym, "trades": trades, "candles": n_prices}
            except Exception as e:
                return {"symbol": sym, "error": f"{type(e).__name__}: {e}"}

    results = await asyncio.gather(*(one(x) for x in syms))
    ok = [r for r in results if "error" not in r]
    failed = [{"symbol": r["symbol"], "error": r["error"]} for r in results if "error" in r]

    def stats(trs):
        w = [t for t in trs if t["pnl"] > 0]
        l = [t for t in trs if t["pnl"] <= 0]
        gw, gl = sum(t["pnl"] for t in w), abs(sum(t["pnl"] for t in l))
        return w, l, gw, gl

    per_symbol = []
    for r in ok:
        trs = r["trades"]
        w, l, gw, gl = stats(trs)
        eq, peak, dd = 0.0, 0.0, 0.0
        for t in trs:
            eq += t["pnl"]
            peak = max(peak, eq)
            dd = max(dd, (peak - eq) / initial_capital * 100)
        per_symbol.append({
            "symbol": r["symbol"], "candles": r["candles"], "trades": len(trs),
            "win_rate": round(len(w) / len(trs) * 100, 1) if trs else 0.0,
            "pnl_pct": round(sum(t["pnl"] for t in trs) / initial_capital * 100, 2),
            "profit_factor": round(gw / gl, 2) if gl > 0 else None,
            "max_drawdown_pct": round(dd, 2),
        })
    per_symbol.sort(key=lambda x: x["pnl_pct"], reverse=True)

    all_trades = sorted((t for r in ok for t in r["trades"]), key=lambda t: t["entry_time"])
    w, l, gw, gl = stats(all_trades)
    n = len(all_trades)
    return {
        "bot_slug": bot_slug, "timeframe": tf, "symbols_source": "manual",
        "symbols_requested": len(syms), "symbols_ok": len(ok), "failed": failed,
        "summary": {
            "total_trades": n, "wins": len(w), "losses": len(l),
            "win_rate": round(len(w) / n * 100, 1) if n else 0.0,
            "avg_trade_pct": round(sum(t["pnl_pct"] for t in all_trades) / n, 2) if n else 0.0,
            "avg_symbol_pnl_pct": round(sum(x["pnl_pct"] for x in per_symbol) / len(per_symbol), 2) if per_symbol else 0.0,
            "profit_factor": round(gw / gl, 2) if gl > 0 else None,
            "worst_symbol_dd_pct": max((x["max_drawdown_pct"] for x in per_symbol), default=0.0),
            "reliable": n >= 30,
        },
        "per_symbol": per_symbol, "trades": all_trades,
    }


@router.get("/compare")
async def compare_bots(
    exchange: ExchangeDep,
    symbols: str,
    tf: str = "1h",
    initial_capital: float = 1000.0,
    fee_pct: float = 0.2,
    days: int = 30,
    start_date: str = Query(None),
    end_date: str = Query(None),
):
    if start_date and end_date:
        exchange = HistoricalExchangeAdapter(start_date, end_date)

    """مقایسه‌ی همه‌ی ربات‌ها روی همان نمادها (فقط خلاصه‌ی هر ربات)."""
    import asyncio

    if not symbols.strip():
        raise HTTPException(status_code=400, detail="حداقل یک نماد لازم است")
    if tf not in ("1h", "4h", "1D"):
        raise HTTPException(status_code=400, detail="مقایسه فقط برای 1h و 4h و 1D پشتیبانی می‌شود")

    sem = asyncio.Semaphore(2)

    async def one(slug: str) -> dict:
        async with sem:
            try:
                r = await run_bot_any(
                    slug, exchange, symbols=symbols, tf=tf,
                    initial_capital=initial_capital, position_size_pct=50.0,
                    fee_pct=fee_pct, days=days,
                )
                return {
                    "bot_slug": slug,
                    "summary": r["summary"],
                    "symbols_ok": r["symbols_ok"],
                    "symbols_requested": r["symbols_requested"],
                    "failed": r["failed"],
                }
            except HTTPException as e:
                return {"bot_slug": slug, "error": str(e.detail)}
            except Exception as e:
                return {"bot_slug": slug, "error": f"{type(e).__name__}: {e}"}

    bots_task = asyncio.gather(*(one(b) for b in ALL_BOTS))
    
    # محاسبه‌ی Buy & Hold برای مقایسه
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    bh_pnls = []
    bh_errors = []
    per_day = {"1h": 24, "4h": 6, "1D": 1}[tf]
    
    for sym in syms:
        try:
            candles = await GetCandlesUseCase(exchange=exchange).execute(
                symbol=sym, timeframe=tf, limit=per_day * days)
            if len(candles) < 2:
                continue
            first_price = float(candles[0].close)
            last_price = float(candles[-1].close)
            pnl_pct = round((last_price / first_price - 1) * 100, 2)
            bh_pnls.append(pnl_pct)
        except Exception as e:
            bh_errors.append(f"{sym}: {type(e).__name__}: {e}")
    
    bh_avg = round(sum(bh_pnls) / len(bh_pnls), 2) if bh_pnls else 0.0
    
    bots = await bots_task
    return {
        "timeframe": tf,
        "symbols": symbols.upper(),
        "bots": bots,
        "buy_hold_avg_pct": bh_avg,
        "buy_hold_errors": bh_errors,
    }
