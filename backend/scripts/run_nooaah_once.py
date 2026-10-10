"""Run Nooaah once — CLI.

Usage (from ~/wallex/backend):
    uv run python -m scripts.run_nooaah_once
    uv run python -m scripts.run_nooaah_once --top 8
"""

from __future__ import annotations

import argparse
import asyncio
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig


def _proposal_to_dict(p) -> dict | None:
    if p is None:
        return None
    return {
        "symbol": p.symbol,
        "action": p.action,
        "entry": round(p.entry, 2),
        "take_profit": round(p.take_profit, 2),
        "stop_loss": round(p.stop_loss, 2),
        "confidence": p.confidence,
        "regime": p.regime,
        "reason": p.reason,
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    configure_logging()
    settings = get_settings()
    exchange = WallexExchange.create(settings)

    try:
        cfg = NooaahConfig(top_n=args.top)
        bot = NooaahBot(exchange=exchange, config=cfg)
        result = await bot.run_once()

        print()
        print("=" * 70)
        print(f"  Nooaah Run — {result.duration_seconds:.1f}s")
        print("=" * 70)
        print(f"  symbols analyzed: {result.symbols_analyzed}")
        print()
        if result.error:
            print(f"  ❌ error: {result.error}")
        elif result.proposal:
            print(f"  🟢 PROPOSAL: {result.proposal.symbol}")
            print(json.dumps(_proposal_to_dict(result.proposal), indent=4, ensure_ascii=False))
        else:
            print("  ⚪ no actionable signal (no trending_up with confidence ≥ threshold)")
        print("=" * 70)
    finally:
        await exchange.aclose()


if __name__ == "__main__":
    asyncio.run(main())
