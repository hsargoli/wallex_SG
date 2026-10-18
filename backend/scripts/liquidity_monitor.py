"""
Liquidity Monitor — checks if Wallex margin liquidity returns for a market.
Runs in background, logs to JSONL, optionally exits on first success.

Usage:
  # One-shot check
  uv run python scripts/liquidity_monitor.py --once

  # Continuous (every 1h) — run in tmux/screen
  uv run python scripts/liquidity_monitor.py --interval 3600

  # Exit as soon as liquidity returns (for CI/alerting)
  uv run python scripts/liquidity_monitor.py --interval 3600 --exit-on-success
"""
import argparse
import asyncio
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

BASE = "https://api.wallex.ir"
LOG_FILE = Path("data/bots/bear_hunter/liquidity_log.jsonl")
MARKET = "BTCTMN"
SIZE = "10000"  # smallest size (if this fails, larger will too)
_STOP = False


def log_event(event: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    event["ts"] = datetime.now(timezone.utc).isoformat()
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    marker = {"OK": "✅", "NO_LIQ": "❌", "ERROR": "🔴"}.get(event.get("status", ""), "•")
    print(f"{marker} [{event['ts'][:19]}] {event.get('status')} — {event.get('message', '')}")


async def check_once(client: httpx.AsyncClient, headers: dict) -> dict:
    try:
        r = await client.get(f"{BASE}/v1/markets")
        all_markets = r.json().get("result", {}).get("symbols", {})
        m = all_markets.get(MARKET, {})
        price = str(m.get("stats", {}).get("lastPrice", "0"))
        if price == "0":
            return {"status": "ERROR", "message": f"{MARKET} price not available"}

        payload = {
            "collateral": SIZE, "market": MARKET, "open_price": price,
            "risk_coef": "1", "side": "short",
            "stop_loss": str(int(float(price) * 1.03)),
            "take_profit": str(int(float(price) * 0.955)),
        }
        r = await client.post(f"{BASE}/margin-trade/v1/public/dry-run", json=payload, headers=headers)
        body = r.json() if r.text else {}
        msg = body.get("message", "")

        if r.status_code == 200:
            result = body.get("result", {})
            return {"status": "OK", "message": f"Liquidity available! liq_price={result.get('liquidity_price')}", "raw": result}
        if r.status_code == 400 and "ظرفیت" in msg:
            return {"status": "NO_LIQ", "message": msg}
        return {"status": f"HTTP_{r.status_code}", "message": msg or r.text[:120]}
    except Exception as e:
        return {"status": "ERROR", "message": f"{type(e).__name__}: {e}"}


async def main() -> None:
    global _STOP
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between checks")
    parser.add_argument("--token", default=None, help="Token (or use WALLEX_VIEW_TOKEN env, or ~/.wallex_view_token)")
    parser.add_argument("--token-file", default=str(Path.home() / ".wallex_view_token"))
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--exit-on-success", action="store_true", help="Exit as soon as liquidity OK")
    args = parser.parse_args()

    # Token resolution
    token = args.token or os.environ.get("WALLEX_VIEW_TOKEN")
    if not token and Path(args.token_file).exists():
        token = Path(args.token_file).read_text().strip()
    if not token:
        print(f"❌ No token. Use --token, WALLEX_VIEW_TOKEN env, or create {args.token_file}")
        sys.exit(1)

    headers = {"x-api-key": token, "Accept": "application/json", "Content-Type": "application/json"}

    def _stop_handler(sig, frame):
        global _STOP
        print("\n⏹️  Stop requested. Exiting after current check...")
        _STOP = True

    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGTERM, _stop_handler)

    log_event({"status": "START", "message": f"market={MARKET} size={SIZE} interval={args.interval}s"})

    async with httpx.AsyncClient(timeout=20) as client:
        while not _STOP:
            result = await check_once(client, headers)
            log_event(result)

            if result["status"] == "OK" and args.exit_on_success:
                log_event({"status": "EXIT", "message": "Liquidity returned. Exiting (--exit-on-success)."})
                return
            if args.once:
                return

            # Sleep in 1s chunks to be responsive to signals
            elapsed = 0
            while elapsed < args.interval and not _STOP:
                await asyncio.sleep(1)
                elapsed += 1

    log_event({"status": "STOPPED", "message": "Monitor stopped by user."})


if __name__ == "__main__":
    asyncio.run(main())
