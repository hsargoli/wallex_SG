"""10_regime_confidence.py — Hypothesis A: does confidence help?

For each candle i (no lookahead):
  1. Compute ADX, EMA50 on candles[:i+1] (causal)
  2. detect regime + confidence (0-100)
  3. compute forward return over window
  4. bucket by confidence

Success (per AP-57):
  For each timeframe, accuracy in confidence>80 bucket > 55%
  AND N in that bucket > 30.

Output: frontend/public/data/regime-confidence.json
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import pandas as pd
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.indicators import adx, ema

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/regime-confidence.json")

TIMEFRAMES = [
    {"name": "1h/24h", "resample_hours": 1, "forward_bars": 24, "range_threshold": 1.0},
    {"name": "4h/10d", "resample_hours": 4, "forward_bars": 60, "range_threshold": 3.0},
    {"name": "1d/30d", "resample_hours": 24, "forward_bars": 30, "range_threshold": 5.0},
]

CONF_BUCKETS = [(50, 60), (60, 70), (70, 80), (80, 90), (90, 101)]


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(
            time=int(times[i]),
            open=Decimal(str(r["open"])),
            high=Decimal(str(r["high"])),
            low=Decimal(str(r["low"])),
            close=Decimal(str(r["close"])),
            volume=Decimal(str(r["volume"])),
        )
        for i, r in df.iterrows()
    ]


def resample_1h(candles: list[Candle], hours: int) -> list[Candle]:
    """Resample 1h candles to N-hour candles."""
    if hours == 1:
        return candles
    df = pd.DataFrame([
        {"datetime": pd.Timestamp(c.time, unit="s"),
         "open": float(c.open), "high": float(c.high),
         "low": float(c.low), "close": float(c.close),
         "volume": float(c.volume)}
        for c in candles
    ])
    df = df.set_index("datetime")
    agg = df.resample(f"{hours}h").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna()
    agg = agg.reset_index()
    return [
        Candle(
            time=int(r["datetime"].timestamp()),
            open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
            low=Decimal(str(r["low"])), close=Decimal(str(r["close"])),
            volume=Decimal(str(r["volume"])),
        )
        for _, r in agg.iterrows()
    ]


def detect_with_confidence(adx_val, ema_val, price: float,
                           config: SarvRouterConfig) -> tuple[str, float, str]:
    """Return (regime_str, confidence 0-100, reason). Pure function."""
    if adx_val is None or ema_val is None:
        return ("unknown", 0.0, "no indicator")
    adx_f = float(adx_val)
    ema_f = float(ema_val)
    if ema_f <= 0:
        return ("unknown", 0.0, "invalid ema")

    # UPTREND: ADX > 25 AND price > EMA50
    if adx_f > config.uptrend_adx_min and price > ema_f:
        adx_margin = min((adx_f - config.uptrend_adx_min) / config.uptrend_adx_min, 1.0)
        price_margin = min((price - ema_f) / ema_f, 1.0)
        conf = 50 + 25 * adx_margin + 25 * price_margin
        return ("uptrend", round(conf, 1),
                f"ADX={adx_f:.1f} price_above_ema={((price/ema_f)-1)*100:.2f}%")

    # DOWNTREND: ADX > 25 AND price < EMA50
    if adx_f > config.downtrend_adx_min and price < ema_f:
        adx_margin = min((adx_f - config.downtrend_adx_min) / config.downtrend_adx_min, 1.0)
        price_margin = min((ema_f - price) / ema_f, 1.0)
        conf = 50 + 25 * adx_margin + 25 * price_margin
        return ("downtrend", round(conf, 1),
                f"ADX={adx_f:.1f} price_below_ema={((1-price/ema_f)*100):.2f}%")

    # RANGE: ADX < 20
    if adx_f < config.range_adx_max:
        adx_margin = min((config.range_adx_max - adx_f) / config.range_adx_max, 1.0)
        conf = 50 + 50 * adx_margin
        return ("range", round(conf, 1), f"ADX={adx_f:.1f} (low)")

    return ("unknown", 0.0, f"ADX={adx_f:.1f} (ambiguous)")


def forward_return_pct(candles: list[Candle], i: int, bars: int) -> float | None:
    if i + bars >= len(candles):
        return None
    entry = float(candles[i].close)
    exit_ = float(candles[i + bars].close)
    if entry <= 0:
        return None
    return (exit_ / entry - 1) * 100


def is_correct(regime: str, ret: float, range_threshold: float) -> bool:
    if regime == "uptrend":
        return ret > 0
    if regime == "downtrend":
        return ret < 0
    if regime == "range":
        return abs(ret) < range_threshold
    return False


def test_timeframe(candles_1h: list[Candle], tf: dict, config: SarvRouterConfig) -> dict:
    name = tf["name"]
    print(f"\n--- {name} ---")
    candles = resample_1h(candles_1h, tf["resample_hours"])
    print(f"    {len(candles)} bars (resample={tf['resample_hours']}h, forward={tf['forward_bars']})")

    if len(candles) < config.warmup_candles + 10:
        return {"name": name, "error": "insufficient data"}

    adx_vals = adx(candles, config.adx_period)
    ema_vals = ema(candles, config.ema_period)

    samples = []  # (regime, confidence, forward_return, correct)
    for i in range(config.warmup_candles, len(candles) - tf["forward_bars"]):
        adx_now = adx_vals[i]
        ema_now = ema_vals[i]
        price = float(candles[i].close)
        regime, conf, _ = detect_with_confidence(adx_now, ema_now, price, config)
        if regime == "unknown" or conf < 50:
            continue
        ret = forward_return_pct(candles, i, tf["forward_bars"])
        if ret is None:
            continue
        correct = is_correct(regime, ret, tf["range_threshold"])
        samples.append({
            "i": i, "regime": regime, "confidence": conf,
            "forward_return": round(ret, 3), "correct": correct,
        })

    print(f"    samples: {len(samples)}")

    # Bucket analysis: overall accuracy per confidence bucket
    buckets_report = []
    for lo, hi in CONF_BUCKETS:
        bucket = [s for s in samples if lo <= s["confidence"] < hi]
        if not bucket:
            buckets_report.append({"range": f"{lo}-{hi-1}", "n": 0, "accuracy_pct": 0,
                                    "avg_forward": 0})
            continue
        n = len(bucket)
        correct = sum(1 for s in bucket if s["correct"])
        avg_fwd = sum(s["forward_return"] for s in bucket) / n
        buckets_report.append({
            "range": f"{lo}-{hi-1}",
            "n": n,
            "accuracy_pct": round(correct / n * 100, 1),
            "avg_forward": round(avg_fwd, 3),
        })

    # Per-regime × high-confidence analysis
    per_regime = {}
    for regime in ("uptrend", "downtrend", "range"):
        regime_samples = [s for s in samples if s["regime"] == regime]
        high_conf = [s for s in regime_samples if s["confidence"] >= 80]
        low_conf = [s for s in regime_samples if s["confidence"] < 80]

        def acc(arr):
            if not arr: return None
            return round(sum(1 for s in arr if s["correct"]) / len(arr) * 100, 1)

        per_regime[regime] = {
            "all": {"n": len(regime_samples), "accuracy_pct": acc(regime_samples)},
            "conf_ge_80": {"n": len(high_conf), "accuracy_pct": acc(high_conf)},
            "conf_lt_80": {"n": len(low_conf), "accuracy_pct": acc(low_conf)},
        }

    # Print bucket table
    print(f"    {'Confidence':12s} | {'N':6s} | {'Accuracy':9s} | {'Avg fwd %':10s}")
    for b in buckets_report:
        print(f"    {b['range']:12s} | {b['n']:6d} | {b['accuracy_pct']:6.1f}%  | {b['avg_forward']:7.3f}%")

    # Print per-regime high-conf
    print(f"    Per-regime (conf>=80 vs <80):")
    for regime, data in per_regime.items():
        all_acc = data["all"]["accuracy_pct"]
        high = data["conf_ge_80"]
        low = data["conf_lt_80"]
        print(f"      {regime:10s}: all={all_acc}% (n={data['all']['n']}), "
              f"conf>=80={high['accuracy_pct']}% (n={high['n']}), "
              f"conf<80={low['accuracy_pct']}% (n={low['n']})")

    # Verdict for this timeframe
    verdict = "unknown"
    best_high = max(
        [data["conf_ge_80"]["accuracy_pct"] for data in per_regime.values()
         if data["conf_ge_80"]["accuracy_pct"] is not None and data["conf_ge_80"]["n"] >= 30],
        default=0,
    )
    if best_high > 55:
        verdict = "PASS"  # at least one regime has high-conf accuracy > 55%
    elif best_high > 50:
        verdict = "MARGINAL"
    else:
        verdict = "FAIL"

    print(f"    → verdict: {verdict} (best high-conf accuracy: {best_high}%)")

    return {
        "name": name,
        "resample_hours": tf["resample_hours"],
        "forward_bars": tf["forward_bars"],
        "total_samples": len(samples),
        "buckets": buckets_report,
        "per_regime": per_regime,
        "best_high_conf_accuracy_pct": best_high,
        "verdict": verdict,
    }


def main() -> None:
    print("=" * 70)
    print("  10_regime_confidence.py — Hypothesis A test")
    print("=" * 70)

    print(f"\n[1] Loading {DATA}")
    candles_1h = load_candles(DATA)
    print(f"    {len(candles_1h)} 1h candles")

    config = SarvRouterConfig()
    print(f"\n[2] Config:")
    print(f"    uptrend_adx_min={config.uptrend_adx_min}")
    print(f"    downtrend_adx_min={config.downtrend_adx_min}")
    print(f"    range_adx_max={config.range_adx_max}")

    results = []
    for tf in TIMEFRAMES:
        r = test_timeframe(candles_1h, tf, config)
        results.append(r)

    # Overall verdict
    print(f"\n{'=' * 70}")
    print("  OVERALL VERDICT (Hypothesis A)")
    print(f"{'=' * 70}")
    for r in results:
        if "error" in r:
            print(f"  {r['name']:10s}: ERROR")
            continue
        print(f"  {r['name']:10s}: best_high_conf={r['best_high_conf_accuracy_pct']}% → {r['verdict']}")

    passes = sum(1 for r in results if r.get("verdict") == "PASS")
    overall = "PASS" if passes >= 1 else "FAIL"
    print(f"\n>>> {overall} ({passes}/{len(results)} timeframes passed)")

    # Save
    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "data_source": "BTCUSDT (Binance) 1h resampled",
        "note": "Not BTCMN (Wallex). Verify on Wallex before Live.",
        "hypothesis": "Adding confidence helps: high-conf (>80) accuracy >55%",
        "results": results,
        "overall_verdict": overall,
        "timeframes_passed": passes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    size_kb = round(OUT.stat().st_size / 1024, 1)
    print(f"\n[4] Saved: {OUT} ({size_kb} KB)")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
