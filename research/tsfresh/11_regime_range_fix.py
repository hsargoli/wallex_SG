"""11_regime_range_fix.py — Hypothesis A + better range metric.

Changes vs 10_regime_confidence.py:
  1. Confidence threshold: 80 → 70 (statistically meaningful)
  2. Range metric: forward_return < X → max_deviation < X
     (measures "did price stay in a band", not "did end price differ")
  3. Baseline: what % of ALL windows are bounded? (for fair comparison)
  4. Lift: how much does ADX improve over baseline?

Success (AP-57):
  - Range accuracy > baseline by 5%+ (ADX actually helps)
  - High-conf (>70) accuracy > 52% on at least one timeframe
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
OUT = Path("frontend/public/data/regime-confidence-fixed.json")

# New: separate threshold for max deviation (range = bounded price)
TIMEFRAMES = [
    {"name": "1h/24h", "resample_hours": 1, "forward_bars": 24,
     "range_max_dev_pct": 3.0},   # ±3% over 24h = range
    {"name": "4h/10d", "resample_hours": 4, "forward_bars": 60,
     "range_max_dev_pct": 8.0},   # ±8% over 10d = range
    {"name": "1d/30d", "resample_hours": 24, "forward_bars": 30,
     "range_max_dev_pct": 15.0},  # ±15% over 30d = range
]

CONF_BUCKETS = [(50, 60), (60, 70), (70, 75), (75, 80), (80, 101)]


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(
            time=int(times[i]),
            open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
            low=Decimal(str(r["low"])), close=Decimal(str(r["close"])),
            volume=Decimal(str(r["volume"])),
        )
        for i, r in df.iterrows()
    ]


def resample_1h(candles: list[Candle], hours: int) -> list[Candle]:
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
    }).dropna().reset_index()
    return [
        Candle(time=int(r["datetime"].timestamp()),
               open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
               low=Decimal(str(r["low"])), close=Decimal(str(r["close"])),
               volume=Decimal(str(r["volume"])))
        for _, r in agg.iterrows()
    ]


def detect_with_confidence(adx_val, ema_val, price: float, config):
    if adx_val is None or ema_val is None:
        return ("unknown", 0.0)
    adx_f, ema_f = float(adx_val), float(ema_val)
    if ema_f <= 0:
        return ("unknown", 0.0)

    if adx_f > config.uptrend_adx_min and price > ema_f:
        m1 = min((adx_f - config.uptrend_adx_min) / config.uptrend_adx_min, 1.0)
        m2 = min((price - ema_f) / ema_f, 1.0)
        return ("uptrend", round(50 + 25 * m1 + 25 * m2, 1))

    if adx_f > config.downtrend_adx_min and price < ema_f:
        m1 = min((adx_f - config.downtrend_adx_min) / config.downtrend_adx_min, 1.0)
        m2 = min((ema_f - price) / ema_f, 1.0)
        return ("downtrend", round(50 + 25 * m1 + 25 * m2, 1))

    if adx_f < config.range_adx_max:
        m1 = min((config.range_adx_max - adx_f) / config.range_adx_max, 1.0)
        return ("range", round(50 + 50 * m1, 1))

    return ("unknown", 0.0)


def forward_return_pct(candles: list[Candle], i: int, bars: int) -> float | None:
    if i + bars >= len(candles):
        return None
    entry = float(candles[i].close)
    exit_ = float(candles[i + bars].close)
    return (exit_ / entry - 1) * 100 if entry > 0 else None


def window_max_dev_pct(candles: list[Candle], i: int, bars: int, entry: float) -> float:
    """Max |high-low vs entry| over the window. NEW range metric."""
    end = min(i + bars + 1, len(candles))
    max_high = max(float(candles[j].high) for j in range(i, end))
    min_low = min(float(candles[j].low) for j in range(i, end))
    dev_up = (max_high - entry) / entry * 100
    dev_down = (entry - min_low) / entry * 100
    return max(dev_up, dev_down)


def is_correct(regime: str, fwd_ret: float, max_dev: float, range_threshold: float) -> bool:
    if regime == "uptrend":
        return fwd_ret > 0
    if regime == "downtrend":
        return fwd_ret < 0
    if regime == "range":
        return max_dev < range_threshold  # NEW: bounded, not directional
    return False


def test_timeframe(candles_1h: list[Candle], tf: dict, config) -> dict:
    name = tf["name"]
    print(f"\n--- {name} ---")
    candles = resample_1h(candles_1h, tf["resample_hours"])
    print(f"    {len(candles)} bars, forward={tf['forward_bars']}, "
          f"range_max_dev={tf['range_max_dev_pct']}%")

    if len(candles) < config.warmup_candles + tf["forward_bars"] + 10:
        return {"name": name, "error": "insufficient data"}

    # BASELINE: what % of ALL windows (regardless of ADX) stay bounded?
    # This is the "random classification" baseline.
    baseline_bounded = 0
    baseline_count = 0
    for i in range(config.warmup_candles, len(candles) - tf["forward_bars"]):
        entry = float(candles[i].close)
        max_dev = window_max_dev_pct(candles, i, tf["forward_bars"], entry)
        baseline_count += 1
        if max_dev < tf["range_max_dev_pct"]:
            baseline_bounded += 1
    baseline_pct = round(baseline_bounded / baseline_count * 100, 1) if baseline_count else 0
    print(f"    baseline (any window is 'range'): {baseline_pct}% "
          f"({baseline_bounded}/{baseline_count})")

    # ADX + EMA
    adx_vals = adx(candles, config.adx_period)
    ema_vals = ema(candles, config.ema_period)

    # Run detection per candle
    samples = []
    for i in range(config.warmup_candles, len(candles) - tf["forward_bars"]):
        adx_now = adx_vals[i]
        ema_now = ema_vals[i]
        price = float(candles[i].close)
        regime, conf = detect_with_confidence(adx_now, ema_now, price, config)
        if regime == "unknown" or conf < 50:
            continue
        fwd_ret = forward_return_pct(candles, i, tf["forward_bars"])
        if fwd_ret is None:
            continue
        max_dev = window_max_dev_pct(candles, i, tf["forward_bars"], price)
        correct = is_correct(regime, fwd_ret, max_dev, tf["range_max_dev_pct"])
        samples.append({
            "regime": regime, "confidence": conf,
            "forward_return": round(fwd_ret, 3),
            "max_deviation": round(max_dev, 3),
            "correct": correct,
        })

    print(f"    classified samples: {len(samples)}")

    # Range-specific: ADX-selected vs baseline
    range_samples = [s for s in samples if s["regime"] == "range"]
    range_bounded = sum(1 for s in range_samples if s["correct"])
    range_acc = round(range_bounded / len(range_samples) * 100, 1) if range_samples else 0
    lift = round(range_acc - baseline_pct, 1)
    print(f"    RANGE: {range_acc}% bounded "
          f"({range_bounded}/{len(range_samples)}) vs baseline {baseline_pct}% "
          f"→ lift {lift:+}%")

    # Per-regime breakdown
    per_regime = {}
    for regime in ("uptrend", "downtrend", "range"):
        rs = [s for s in samples if s["regime"] == regime]
        high = [s for s in rs if s["confidence"] >= 70]

        def acc(arr):
            return round(sum(1 for s in arr if s["correct"]) / len(arr) * 100, 1) if arr else None

        per_regime[regime] = {
            "all": {"n": len(rs), "accuracy_pct": acc(rs)},
            "conf_ge_70": {"n": len(high), "accuracy_pct": acc(high)},
        }

    # Confidence buckets (overall)
    bucket_report = []
    for lo, hi in CONF_BUCKETS:
        b = [s for s in samples if lo <= s["confidence"] < hi]
        if not b:
            bucket_report.append({"range": f"{lo}-{hi-1}", "n": 0, "accuracy_pct": None})
            continue
        acc_val = round(sum(1 for s in b if s["correct"]) / len(b) * 100, 1)
        bucket_report.append({"range": f"{lo}-{hi-1}", "n": len(b), "accuracy_pct": acc_val})

    # Verdict
    best_high_conf = max(
        [per_regime[r]["conf_ge_70"]["accuracy_pct"]
         for r in per_regime
         if per_regime[r]["conf_ge_70"]["accuracy_pct"] is not None
         and per_regime[r]["conf_ge_70"]["n"] >= 100],
        default=0,
    )
    # For range specifically, use lift over baseline
    range_ok = lift > 5 and len(range_samples) >= 30

    print(f"\n    confidence buckets:")
    for b in bucket_report:
        print(f"      {b['range']:8s}: n={b['n']:6d}, acc={b['accuracy_pct']}%")

    print(f"\n    per-regime (conf>=70):")
    for r, d in per_regime.items():
        print(f"      {r:10s}: all={d['all']['accuracy_pct']}% (n={d['all']['n']}), "
              f"high-conf={d['conf_ge_70']['accuracy_pct']}% (n={d['conf_ge_70']['n']})")

    verdict = "PASS" if best_high_conf > 52 else ("MARGINAL" if best_high_conf > 48 else "FAIL")
    print(f"    → trend verdict: {verdict} (best high-conf acc: {best_high_conf}%)")
    print(f"    → range verdict: {'PASS' if range_ok else 'FAIL'} (lift: {lift:+}% over baseline)")

    return {
        "name": name,
        "bars": len(candles),
        "forward_bars": tf["forward_bars"],
        "range_max_dev_pct": tf["range_max_dev_pct"],
        "samples": len(samples),
        "baseline_bounded_pct": baseline_pct,
        "range_accuracy_pct": range_acc,
        "range_lift_vs_baseline": lift,
        "range_verdict": "PASS" if range_ok else "FAIL",
        "buckets": bucket_report,
        "per_regime": per_regime,
        "best_high_conf_accuracy_pct": best_high_conf,
        "trend_verdict": verdict,
    }


def main() -> None:
    print("=" * 70)
    print("  11_regime_range_fix.py — Hypothesis A + better range metric")
    print("=" * 70)

    print(f"\n[1] Loading {DATA}")
    candles_1h = load_candles(DATA)
    print(f"    {len(candles_1h)} 1h candles")

    config = SarvRouterConfig()
    results = [test_timeframe(candles_1h, tf, config) for tf in TIMEFRAMES]

    # Overall
    print(f"\n{'=' * 70}")
    print("  FINAL VERDICT")
    print(f"{'=' * 70}")
    trend_pass = sum(1 for r in results if r.get("trend_verdict") == "PASS")
    range_pass = sum(1 for r in results if r.get("range_verdict") == "PASS")
    for r in results:
        if "error" in r:
            continue
        print(f"  {r['name']:10s}: trend={r['trend_verdict']:8s} "
              f"({r['best_high_conf_accuracy_pct']}%) | "
              f"range={r['range_verdict']:8s} "
              f"(lift {r['range_lift_vs_baseline']:+}%)")

    print(f"\n>>> TREND: {trend_pass}/{len(results)} PASS")
    print(f">>> RANGE: {range_pass}/{len(results)} PASS")
    overall = "PASS" if (trend_pass >= 1 and range_pass >= 1) else "FAIL"
    print(f">>> OVERALL: {overall}")

    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "data_source": "BTCUSDT (Binance) 1h resampled",
        "hypothesis": "Confidence>=70 helps trend; max-deviation range metric beats baseline",
        "config": {
            "uptrend_adx_min": config.uptrend_adx_min,
            "downtrend_adx_min": config.downtrend_adx_min,
            "range_adx_max": config.range_adx_max,
        },
        "results": results,
        "trend_passed": trend_pass,
        "range_passed": range_pass,
        "overall_verdict": overall,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[2] Saved: {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
