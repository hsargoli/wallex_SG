"""تست ترکیب‌های مختلف TP/SL."""

import asyncio
from dataclasses import dataclass, field

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import build_features, candles_to_df, load_model

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TIMEFRAME = "15m"
N_CANDLES = 1000
WARMUP = 100
MAX_DURATION = 24
FEE_PCT = 0.2
ML_STRONG = 0.55

# ۴ ترکیب
COMBOS = [
    (2.0, 1.5, "TP=2.0, SL=1.5"),
    (2.0, 1.0, "TP=2.0, SL=1.0"),
    (2.5, 1.5, "TP=2.5, SL=1.5"),
    (3.0, 1.5, "TP=3.0, SL=1.5"),
    (1.5, 1.0, "TP=1.5, SL=1.0 (قبلی)"),
]


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TIMEFRAME, limit=N_CANDLES)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


@dataclass
class Stats:
    name: str
    trades: list = field(default_factory=list)
    @property
    def total(self): return len(self.trades)
    @property
    def wins(self): return sum(1 for t in self.trades if t > 0)
    @property
    def losses(self): return sum(1 for t in self.trades if t <= 0)
    @property
    def wr(self): return (self.wins / self.total * 100) if self.total else 0
    @property
    def total_return(self):
        if not self.trades: return 0
        eq = 1.0
        for r in self.trades:
            eq *= (1 + r / 100)
        return (eq - 1) * 100


def run_strategy(name, markets_data, model, tp_pct, sl_pct):
    stats = Stats(name=name)
    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        X_all = build_features(df)
        
        # Batch predict
        ml_probs = [None] * len(X_all)
        valid_mask = ~X_all.isna().any(axis=1)
        if valid_mask.sum() > 0:
            X_valid = X_all[valid_mask]
            probs = model.predict_proba(X_valid)[:, 1]
            for i, idx in enumerate(X_valid.index):
                ml_probs[idx] = float(probs[i])
        
        open_pos = None
        for idx in range(WARMUP, len(candles)):
            candle = candles[idx]
            
            # خروج
            if open_pos is not None:
                exit_price = None
                if candle.high >= open_pos["tp"]:
                    exit_price = open_pos["tp"]
                elif candle.low <= open_pos["sl"]:
                    exit_price = open_pos["sl"]
                elif idx - open_pos["entry_idx"] >= MAX_DURATION:
                    exit_price = float(candle.close)
                
                if exit_price is not None:
                    ret = (float(exit_price) / open_pos["entry"] - 1) * 100 - FEE_PCT
                    stats.trades.append(ret)
                    open_pos = None
            
            # ورود
            if open_pos is not None:
                continue
            
            ml_prob = ml_probs[idx]
            rule = detect_bottom(candles, idx=idx)
            
            # استراتژی OR
            should_enter = (
                (ml_prob is not None and ml_prob >= ML_STRONG)
                or (rule.is_bottom and rule.score >= 5)
            )
            if not should_enter:
                continue
            
            entry = float(candle.close)
            open_pos = {
                "entry": entry,
                "tp": entry * (1 + tp_pct / 100),
                "sl": entry * (1 - sl_pct / 100),
                "entry_idx": idx,
            }
    
    return stats


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")
    
    print("🧠 لود مدل ML...")
    model = load_model()
    print("✅ لود شد\n")
    
    print(f"{'='*70}")
    print(f"{'TP / SL':<25} {'ترید':>6} {'WR':>8} {'بازده':>10} {'میانگین سود':>12} {'میانگین ضرر':>12}")
    print(f"{'='*70}")
    
    results = []
    for tp, sl, name in COMBOS:
        stats = run_stats = run_strategy(name, markets_data, model, tp, sl)
        wins = [t for t in stats.trades if t > 0]
        losses = [t for t in stats.trades if t <= 0]
        avg_w = sum(wins) / len(wins) if wins else 0
        avg_l = sum(losses) / len(losses) if losses else 0
        print(f"{name:<25} {stats.total:>6} {stats.wr:>7.1f}% {stats.total_return:>+9.2f}% {avg_w:>+11.2f}% {avg_l:>+11.2f}%")
        results.append((stats, name))
    
    # بهترین
    valid = [r for r in results if r[0].total >= 5]
    if valid:
        best = max(valid, key=lambda x: x[0].total_return)
        print(f"\n🏆 بهترین: {best[1]}  →  بازده {best[0].total_return:+.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
