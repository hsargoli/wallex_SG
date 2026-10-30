"""Generate per-bot report JSON from existing data sources.

Output: backend/data/bots/{slug}/{backtest,paper,meta}.json
Sources (in priority order per bot):
    paper:    nooaah/state.json, sarv_router/users/*.json
    backtest: BASELINE_*.json, backtest_results/*.json
    meta:     BotInfo from registry

Missing data → {"status": "no_data"} (fail-safe, never crashes UI).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_DIR = Path("data")
OUT_DIR = DATA_DIR / "bots"
BASELINE_DIR = Path("../docs/reports/backtest")

# Active bots (per CTO red line)
ACTIVE = {"sarv_router", "nooaah"}
ARCHIVED = {
    "trend_follow", "grid_bot", "volatility_hunter",
    "volatility_hunter_v2", "mean_revert", "smart_portfolio",
    "market_scanner", "scalp_master", "sarv_tiger",
}


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _write(slug: str, kind: str, payload: dict) -> None:
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{kind}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
    )


def build_paper(slug: str) -> dict:
    if slug == "nooaah":
        d = _load(DATA_DIR / "nooaah" / "state.json")
        if not d:
            return {"status": "no_data"}
        return {
            "status": "ok",
            "mode": d.get("mode", "paper"),
            "started_at": d.get("paper_started_at", 0),
            "last_run": d.get("last_run", 0),
            "capital_total": d.get("capital_total", 0.0),
            "capital_available": d.get("capital_available", 0.0),
            "open_positions": len(d.get("open_positions", [])),
            "closed_trades": len(d.get("closed_trades", [])),
            "daily_pnl_pct": d.get("daily_pnl_pct", 0.0),
            "killed": d.get("killed", False),
            "consecutive_losses": d.get("consecutive_losses", 0),
            "live_stage": d.get("live_stage", 0),
            "source": "data/nooaah/state.json",
        }
    if slug == "sarv_router":
        users_dir = DATA_DIR / "sarv_router" / "users"
        d = _load(users_dir / "production-default.json") if users_dir.exists() else None
        gate = _load(DATA_DIR / "sarv_router" / "gate.json") or {}
        if not d:
            return {"status": "no_data"}
        return {
            "status": "ok",
            "regime": d.get("current_regime", "unknown"),
            "regime_since_idx": d.get("regime_since_idx"),
            "active_bots": d.get("active_bots", []),
            "allocations": d.get("allocations", {}),
            "capital_total": d.get("total_capital", 0.0),
            "cash": d.get("cash", 0.0),
            "daily_pnl_pct": d.get("daily_pnl_pct", 0.0),
            "kill_switch_manual": d.get("kill_switch_manual", False),
            "kill_switch_auto": d.get("kill_switch_auto", False),
            "gate": gate,
            "source": "data/sarv_router/",
        }
    return {"status": "archived", "note": "این ربات آرشیو شده است. آمار backtest برای مرجع."}


def build_backtest(slug: str) -> dict:
    """Merge all available backtest sources for this bot."""
    sources = {}

    # Source 1: backtest_results/*.json — per-bot keys
    br_dir = DATA_DIR / "backtest_results"
    if br_dir.exists():
        for f in sorted(br_dir.glob("*.json")):
            d = _load(f)
            if isinstance(d, dict) and slug in d:
                sources[f.name] = d[slug]

    # Source 2: BASELINE_*.json (bear_hunter only historically)
    if BASELINE_DIR.exists():
        for f in sorted(BASELINE_DIR.glob("BASELINE_*.json")):
            d = _load(f)
            if not isinstance(d, dict):
                continue
            if all(k.startswith("Q") for k in d.keys()):
                if slug == "bear_hunter":
                    sources[f.name] = d

    if not sources:
        return {"status": "no_data"}

    return {"status": "ok", "sources": sources}


def build_meta(slug: str) -> dict:
    try:
        from app.services.bots import bot_registry  # lazy
        bot_registry._ensure_registered() if hasattr(bot_registry, "_ensure_registered") else None
        bot = bot_registry.get(slug) if hasattr(bot_registry, "get") else None
        if bot:
            info = bot.info
            return {
                "status": "ok",
                "slug": info.slug,
                "name": info.name,
                "name_en": info.name_en,
                "version": info.version,
                "description": info.description,
                "tags": list(info.tags),
                "capabilities": list(info.capabilities),
                "tier": info.tier,
                "author": info.author,
                "archived": slug in ARCHIVED,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}

    return {"status": "no_data", "archived": slug in ARCHIVED}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", nargs="*", default=None)
    args = ap.parse_args()

    all_slugs = sorted(ACTIVE | ARCHIVED)
    slugs = args.slugs or all_slugs

    print(f"output: {OUT_DIR}")
    print(f"slugs:  {len(slugs)}")
    print()

    now = datetime.now(timezone.utc).isoformat()
    for slug in slugs:
        paper = build_paper(slug)
        backtest = build_backtest(slug)
        meta = build_meta(slug)
        _write(slug, "paper", paper)
        _write(slug, "backtest", backtest)
        _write(slug, "meta", meta)

        status = "archived" if slug in ARCHIVED else "active"
        bt = backtest.get("status", "?")
        pp = paper.get("status", "?")
        print(f"  {slug:22s}  [{status}]  backtest={bt:8s}  paper={pp}")

    print()
    print(f"✅ generated at {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
