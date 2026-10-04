"""
BotSimulator — شبیه‌ساز واقع‌بینانه ربات‌ها.

رفع بایاس‌ها:
  ۱. Look-ahead bias:
     - تصمیم ربات در close کندل i گرفته می‌شه
     - ورود/خروج در OPEN کندل i+1 اجرا می‌شه (نه close جاری)
  ۲. کارمزد:
     - از config ربات (fee_pct) خونده می‌شه
     - در ورود و خروج کسر می‌شه (fee_rate = fee_pct / 100)
  ۳. Position Sizing:
     - از config ربات (position_size_pct) خونده می‌شه
     - فقط بخشی از cash درگیر می‌شه، نه ۱۰۰٪
  ۴. SL/TP:
     - با high/low کندل چک می‌شه (نه فقط close)
     - اجرا با قیمت دقیق SL/TP (با احتساب fee)
"""

from typing import Optional, List
from app.domain.entities.candle import Candle


# ============================================================
# Base Adapter
# ============================================================
class BaseBotAdapter:
    """اینترفیس پایه‌ی Adapter ربات‌ها."""

    slug: str = ""
    timeframe: str = "1D"

    @property
    def fee_pct(self) -> float:
        """کارمزد هر معامله (درصد)."""
        return float(getattr(self.config, "fee_pct", 0.2))

    @property
    def position_size_pct(self) -> float:
        """درصد سرمایه درگیر در هر معامله."""
        return float(getattr(self.config, "position_size_pct", 100.0))

    def on_candle(self, candles: List[Candle], position: Optional[dict]) -> dict:
        """
        ورودی: کندل‌های تا i (شامل)، وضعیت پوزیشن
        خروجی:
            {"action": "hold"}
            {"action": "enter", "reason": str, "meta": {"sl": float, "tp": float|None, ...}}
            {"action": "exit", "reason": str}
            {"action": "update", "meta": {...}}   # آپدیت SL مثلاً
        """
        raise NotImplementedError


# ============================================================
# Trend Follow Adapter
# ============================================================
class TrendFollowAdapter(BaseBotAdapter):
    slug = "trend_follow"

    def __init__(self):
        from app.services.bots.trend_follow.config import TrendFollowConfig
        self.config = TrendFollowConfig()
        self.timeframe = self.config.timeframe

    def on_candle(self, candles, position):
        from app.services.bots.trend_follow.strategy import evaluate_entry, evaluate_exit

        if position is None:
            signal = evaluate_entry(candles, self.config)
            if signal is None:
                return {"action": "hold"}
            return {
                "action": "enter",
                "reason": signal.reason,
                "meta": {
                    "sl": signal.initial_sl,
                    "trail": signal.trailing_distance,
                },
            }

        exit_sig = evaluate_exit(
            candles=candles,
            entry_price=position["entry_price"],
            current_sl=position["sl"],
            trailing_distance=position["trail"],
            config=self.config,
            candles_in_position=position["candles_in_position"],
        )

        if exit_sig.should_exit:
            # اگه trailing_sl زده شد، SL فعلی قیمت خروجه
            if exit_sig.reason in ("trailing_sl", "initial_sl"):
                return {
                    "action": "exit",
                    "reason": exit_sig.reason,
                    "exit_price": position["sl"],
                }
            return {"action": "exit", "reason": exit_sig.reason}

        if exit_sig.new_sl is not None and exit_sig.new_sl > position["sl"]:
            return {"action": "update", "meta": {"sl": exit_sig.new_sl}}

        return {"action": "hold"}


# ============================================================
# Volatility Hunter Adapter
# ============================================================
class VolatilityHunterAdapter(BaseBotAdapter):
    slug = "volatility_hunter"

    def __init__(self):
        from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
        self.config = VolatilityHunterConfig()
        self.timeframe = self.config.timeframe

    def on_candle(self, candles, position):
        from app.services.bots.volatility_hunter.strategy import evaluate_entry, evaluate_exit

        if position is None:
            signal = evaluate_entry(candles, self.config)
            if signal is None or not signal.should_trade or signal.action != "buy":
                return {"action": "hold"}
            return {
                "action": "enter",
                "reason": signal.reason,
                "meta": {
                    "sl": signal.stop_loss,
                    "tp": signal.take_profit,
                },
            }

        should_exit, exit_price, reason = evaluate_exit(
            candles=candles,
            entry_price=position["entry_price"],
            stop_loss=position["sl"],
            take_profit=position["tp"],
            config=self.config,
        )

        if should_exit:
            # برای stop_loss و take_profit: قیمت دقیق SL/TP
            if reason in ("stop_loss", "take_profit"):
                return {"action": "exit", "reason": reason, "exit_price": exit_price}
            return {"action": "exit", "reason": reason}

        return {"action": "hold"}


# ============================================================
# Mean Revert Adapter (کف‌زن)
# ============================================================
class MeanRevertAdapter(BaseBotAdapter):
    """
    آداپتور کف‌زن — Simple Bot / Bounce Scalper روی تایم‌فریم 1h.

    ⚠️ نکته: پارامترهای اصلی این استراتژی برای 15m بهینه شدن.
    چون والکس فقط 1h و 1D رو درست پشتیبانی می‌کنه، ما روی 1h اجرا می‌کنیم
    و پارامترهای SL/TP رو متناسب با کندل 1h بزرگ‌تر می‌کنیم (scale ≈ 2x).

    منطق:
      ۱. اگه Symbol در strategy_config.json ثبت شده → از استراتژی بهینه‌ش استفاده کن
      ۲. در غیر این صورت → fallback به Bounce Scalper
    """

    slug = "mean_revert"

    # تنظیمات متناسب با تایم‌فریم 1h
    TF_TIMEOUT = 24          # 24 ساعت
    TF_SL_PCT = 3.0          # 3.0% (به جای 1.5%)
    TF_TP_PCT = 4.0          # 4.0% (به جای 2.0%)

    def __init__(self):
        from app.services.bots.mean_revert.config import MeanRevertConfig
        self.config = MeanRevertConfig()
        self.timeframe = "1h"   # اجبار به 1h (چون والکس 15m رو ناقص می‌ده)
        self._dispatcher = None
        self._symbol = "BTCUSDT"

    def set_symbol(self, symbol: str):
        self._symbol = symbol

    @property
    def dispatcher(self):
        if self._dispatcher is None:
            from app.services.smart_dispatcher import dispatcher
            self._dispatcher = dispatcher
        return self._dispatcher

    # ------------------------------------------------------------
    # تصمیم ورود (Dispatcher + Fallback)
    # ------------------------------------------------------------
    def _get_entry_decision(self, candles):
        """تصمیم ورود + تنظیم SL/TP برای تایم‌فریم 1h."""

        # تلاش اول: SmartDispatcher
        d = None
        try:
            d = self.dispatcher.make_decision(self._symbol, candles)
        except Exception:
            d = None

        # Fallback: Bounce Scalper مستقیم
        if d is None:
            from app.services.bounce_scalper import make_bounce_decision
            bd = make_bounce_decision(candles)
            d = {
                "should_trade": bd.should_trade,
                "action": bd.action,
                "entry": bd.entry_price,
                "tp": bd.take_profit,
                "sl": bd.stop_loss,
                "reason": f"[BOUNCE] {bd.reason}",
                "strategy": "bounce",
            }

        if not d.get("should_trade"):
            return d

        # ------------------------------------------------------------
        # تنظیم SL/TP برای 1h
        # استراتژی اصلی برای 15m تنظیم شده. تو 1h نوسان ۴ برابر بیشتره
        # پس SL/TP رو از روی درصدهای 1h بازنویسی می‌کنیم.
        # ------------------------------------------------------------
        entry = float(candles[-1].close)
        sl = entry * (1 - self.TF_SL_PCT / 100)
        tp = entry * (1 + self.TF_TP_PCT / 100)

        d["entry"] = entry
        d["sl"] = sl
        d["tp"] = tp
        d["reason"] = d.get("reason", "") + f" [1h-scaled SL={self.TF_SL_PCT}% TP={self.TF_TP_PCT}%]"
        return d

    # ------------------------------------------------------------
    # on_candle
    # ------------------------------------------------------------
    def on_candle(self, candles, position, symbol=None):
        if symbol:
            self._symbol = symbol

        # ---------- تصمیم ورود ----------
        if position is None:
            decision = self._get_entry_decision(candles)
            if not decision:
                return {"action": "hold"}
            if not decision.get("should_trade"):
                return {"action": "hold"}
            if decision.get("action") != "buy":
                return {"action": "hold"}

            sl = decision.get("sl")
            tp = decision.get("tp")

            # اعتبارسنجی SL/TP
            if not sl or not tp or sl <= 0 or tp <= 0:
                return {"action": "hold"}

            return {
                "action": "enter",
                "reason": decision.get("reason", ""),
                "meta": {
                    "sl": float(sl),
                    "tp": float(tp),
                },
            }

        # ---------- تصمیم خروج ----------
        # Timeout (بر اساس تنظیمات 1h)
        if position["candles_in_position"] >= self.TF_TIMEOUT:
            return {"action": "exit", "reason": "timeout"}

        return {"action": "hold"}


# ============================================================
# Volatility Hunter v2 Adapter
# ============================================================
class VolatilityHunterV2Adapter(BaseBotAdapter):
    """آداپتور نوسان‌گیر v2 — با فیلترهای بهبودیافته."""

    slug = "volatility_hunter_v2"

    def __init__(self):
        from app.services.bots.volatility_hunter_v2.config import (
            VolatilityHunterV2Config,
        )
        self.config = VolatilityHunterV2Config()
        self.timeframe = self.config.timeframe

    def on_candle(self, candles, position):
        from app.services.bots.volatility_hunter_v2.strategy import (
            evaluate_entry_v2,
            evaluate_exit_v2,
        )

        if position is None:
            signal = evaluate_entry_v2(candles, self.config)
            if signal is None or not signal.should_trade:
                return {"action": "hold"}
            return {
                "action": "enter",
                "reason": signal.reason,
                "meta": {
                    "sl": signal.stop_loss,
                    "tp": signal.take_profit,
                },
            }

        should_exit, exit_price, reason = evaluate_exit_v2(
            candles=candles,
            entry_price=position["entry_price"],
            stop_loss=position["sl"],
            take_profit=position["tp"],
            config=self.config,
            candles_in_position=position["candles_in_position"],
        )

        if should_exit:
            if reason in ("stop_loss", "take_profit"):
                return {
                    "action": "exit",
                    "reason": reason,
                    "exit_price": exit_price,
                }
            return {"action": "exit", "reason": reason}

        return {"action": "hold"}


# ============================================================
# Registry
# ============================================================
ADAPTERS = {
    "trend_follow": TrendFollowAdapter,
    "volatility_hunter": VolatilityHunterAdapter,
    "volatility_hunter_v2": VolatilityHunterV2Adapter,
    "mean_revert": MeanRevertAdapter,
}


def list_simulatable_bots() -> List[str]:
    return list(ADAPTERS.keys())


# ============================================================
# BotSimulator
# ============================================================
class BotSimulator:
    """شبیه‌ساز مبتنی بر ربات با اجرای واقع‌بینانه."""

    def __init__(self, repository, bot_slug: str, initial_balance: float = 1000.0):
        if bot_slug not in ADAPTERS:
            raise ValueError(
                f"ربات '{bot_slug}' پشتیبانی نمی‌شود. "
                f"ربات‌های موجود: {', '.join(ADAPTERS.keys())}"
            )
        self.repository = repository
        self.bot_slug = bot_slug
        self.adapter: BaseBotAdapter = ADAPTERS[bot_slug]()
        self.initial_balance = initial_balance

    async def run(self, start_date: str, end_date: str, symbol: str = "BTCUSDT"):
        candles = self.repository.get_candles(
            symbol, start_date, end_date, timeframe=self.adapter.timeframe,
        )

        if not candles or len(candles) < 2:
            return {
                "status": "error",
                "message": (
                    f"داده‌ای برای نماد {symbol} در بازه {start_date} تا {end_date} "
                    f"با تایم‌فریم {self.adapter.timeframe} یافت نشد. "
                    f"توجه: والکس برای تایم‌فریم 1h فقط حدود ۳۰ روز اخیر را پشتیبانی می‌کند."
                ),
                "pnl_report": {
                    "initial_balance": self.initial_balance,
                    "final_balance": self.initial_balance,
                    "total_pnl": 0.0,
                    "pnl_pct": 0.0,
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0,
                },
            }

        fee_rate = self.adapter.fee_pct / 100.0
        size_pct = self.adapter.position_size_pct / 100.0

        cash = self.initial_balance
        position: Optional[dict] = None
        pending_entry: Optional[dict] = None
        pending_exit: Optional[str] = None
        trades: List[dict] = []

        # اگه Adapter متد set_symbol داره، symbol رو بهش بدیم
        if hasattr(self.adapter, "set_symbol"):
            self.adapter.set_symbol(symbol)

        for i, candle in enumerate(candles):
            o = float(candle.open)
            h = float(candle.high)
            l = float(candle.low)

            # ------------------------------------------------------------
            # ۱) اجرای pending orders با OPEN این کندل
            # ------------------------------------------------------------
            if pending_entry is not None and position is None:
                size_usd = cash * size_pct
                entry_price = o * (1 + fee_rate)   # fee در قیمت لحاظ می‌شه
                qty = size_usd / entry_price
                cash -= size_usd
                position = {
                    "entry_price": entry_price,
                    "qty": qty,
                    "size_usd": size_usd,
                    "sl": pending_entry["meta"].get("sl"),
                    "tp": pending_entry["meta"].get("tp"),
                    "trail": pending_entry["meta"].get("trail"),
                    "entry_i": i,
                    "candles_in_position": 0,
                }
                trades.append({
                    "i": i,
                    "side": "BUY",
                    "price": round(entry_price, 2),
                    "reason": pending_entry.get("reason", ""),
                    "size_usd": round(size_usd, 2),
                })
                pending_entry = None

            elif pending_exit is not None and position is not None:
                exit_price = o * (1 - fee_rate)
                proceeds = position["qty"] * exit_price
                cash += proceeds
                pnl = proceeds - position["size_usd"]
                trades.append({
                    "i": i,
                    "side": "SELL",
                    "price": round(exit_price, 2),
                    "reason": pending_exit,
                    "pnl": round(pnl, 2),
                })
                position = None
                pending_exit = None

            # ------------------------------------------------------------
            # ۲) چک SL/TP با high/low این کندل
            # ------------------------------------------------------------
            if position is not None:
                sl = position.get("sl")
                tp = position.get("tp")
                exit_reason = None
                exit_base_price = None

                # SL اول چک می‌شه (محافظه‌کارانه)
                if sl is not None and l <= sl:
                    exit_reason = "stop_loss"
                    exit_base_price = sl
                elif tp is not None and h >= tp:
                    exit_reason = "take_profit"
                    exit_base_price = tp

                if exit_reason:
                    exit_price = exit_base_price * (1 - fee_rate)
                    proceeds = position["qty"] * exit_price
                    cash += proceeds
                    pnl = proceeds - position["size_usd"]
                    trades.append({
                        "i": i,
                        "side": "SELL",
                        "price": round(exit_price, 2),
                        "reason": exit_reason,
                        "pnl": round(pnl, 2),
                    })
                    position = None

            # ------------------------------------------------------------
            # ۳) تصمیم ربات (اجرا در کندل بعدی)
            # ------------------------------------------------------------
            if position is None and pending_entry is None and pending_exit is None:
                action = self.adapter.on_candle(candles[: i + 1], None)
                if action["action"] == "enter":
                    pending_entry = action
            elif position is not None and pending_exit is None:
                position["candles_in_position"] += 1
                action = self.adapter.on_candle(candles[: i + 1], position)
                if action["action"] == "exit":
                    pending_exit = action.get("reason", "signal")
                elif action["action"] == "update":
                    meta = action.get("meta", {})
                    if "sl" in meta:
                        position["sl"] = meta["sl"]

        # ------------------------------------------------------------
        # ۴) بستن اجباری پوزیشن باز در پایان
        # ------------------------------------------------------------
        if position is not None:
            last_close = float(candles[-1].close)
            exit_price = last_close * (1 - fee_rate)
            proceeds = position["qty"] * exit_price
            cash += proceeds
            pnl = proceeds - position["size_usd"]
            trades.append({
                "i": len(candles) - 1,
                "side": "SELL",
                "price": round(exit_price, 2),
                "reason": "end_of_backtest",
                "pnl": round(pnl, 2),
                "forced": True,
            })
            position = None

        total_pnl = cash - self.initial_balance
        completed = [t for t in trades if t["side"] == "SELL"]
        wins = [t for t in completed if t.get("pnl", 0) > 0]
        losses = [t for t in completed if t.get("pnl", 0) <= 0]

        return {
            "status": "success",
            "symbol": symbol,
            "bot_slug": self.bot_slug,
            "timeframe": self.adapter.timeframe,
            "fee_pct": self.adapter.fee_pct,
            "position_size_pct": self.adapter.position_size_pct,
            "prices_count": len(candles),
            "trades": trades,
            "pnl_report": {
                "initial_balance": self.initial_balance,
                "final_balance": round(cash, 2),
                "total_pnl": round(total_pnl, 2),
                "pnl_pct": round((total_pnl / self.initial_balance) * 100, 2),
                "total_trades": len(completed),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": round(len(wins) / len(completed) * 100, 1) if completed else 0,
            },
        }
