"""اندازه‌گیری دقیق محدودیت‌های API والکس.

برای هر resolution ممکن، بازه‌های مختلف را تست می‌کند
و نتایج را در JSON ذخیره می‌کند.

استفاده:
    cd ~/wallex/backend
    PYTHONPATH=. uv run python scripts/tools/measure_api_limits.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://api.wallex.ir"
SYMBOL = "BTCTMN"

# همه resolutionهای ممکن (اعم از مستند و نامستند)
RESOLUTIONS = ["1", "5", "15", "30", "60", "240", "480", "720", "1D", "1W"]

# بازه‌های مختلف (به روز)
PERIODS_DAYS = [1, 2, 3, 7, 14, 30, 60, 90, 180, 365, 730]

OUTPUT_DIR = Path("data/api_limits")


def measure_one(
    resolution: str, days: int, session: requests.Session
) -> dict:
    """یک درخواست به والکس و ثبت نتیجه."""
    now = int(datetime.now(timezone.utc).timestamp())
    from_ts = now - (days * 24 * 3600)

    result = {
        "resolution": resolution,
        "days": days,
        "from_ts": from_ts,
        "to_ts": now,
        "status_code": None,
        "s": None,
        "candles": 0,
        "first_candle_time": None,
        "last_candle_time": None,
        "actual_span_days": None,
        "error": None,
    }

    try:
        r = session.get(
            f"{BASE_URL}/v1/udf/history",
            params={
                "symbol": SYMBOL,
                "resolution": resolution,
                "from": from_ts,
                "to": now,
            },
            timeout=30,
        )
        result["status_code"] = r.status_code
        data = r.json()
        result["s"] = data.get("s")

        times = data.get("t", [])
        result["candles"] = len(times)

        if times:
            result["first_candle_time"] = times[0]
            result["last_candle_time"] = times[-1]
            span_seconds = times[-1] - times[0]
            result["actual_span_days"] = round(span_seconds / 86400, 2)

    except Exception as e:
        result["error"] = str(e)[:200]

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    all_results = []

    print("=" * 90)
    print(f"اندازه‌گیری محدودیت‌های API والکس — نماد {SYMBOL}")
    print(f"زمان: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 90)
    print()
    print(
        f"{'resolution':10s} | {'days':5s} | {'s':6s} | "
        f"{'candles':8s} | {'span_days':10s}"
    )
    print("-" * 90)

    for res in RESOLUTIONS:
        for days in PERIODS_DAYS:
            r = measure_one(res, days, session)
            all_results.append(r)

            s = r["s"] or "?"
            n = r["candles"]
            span = r["actual_span_days"] if r["actual_span_days"] is not None else "-"
            print(f"{res:10s} | {days:5d} | {s:6s} | {n:8d} | {str(span):10s}")

            # مکث کوتاه برای rate limit
            time.sleep(0.3)

        print()  # خط خالی بین resolutionها

    # ذخیره
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_path = OUTPUT_DIR / f"measurement_{today}.json"
    out_path.write_text(
        json.dumps(
            {
                "measured_at": datetime.now(timezone.utc).isoformat(),
                "symbol": SYMBOL,
                "resolutions": RESOLUTIONS,
                "periods_days": PERIODS_DAYS,
                "results": all_results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"ذخیره شد: {out_path}")


if __name__ == "__main__":
    main()
