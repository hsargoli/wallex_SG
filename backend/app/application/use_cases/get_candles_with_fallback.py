"""UseCase: دریافت کندل با شبیه‌سازی fallback از تایم‌فریم بالاتر."""

import time
from dataclasses import dataclass
from decimal import Decimal

from app.application.use_cases.candles_fallback_types import (
    CandlesWithFallback,
    SyntheticRange,
)
from app.domain.entities.candle import Candle
from app.domain.ports.exchange import ExchangePort

# ─── محدودیت 15m ───
MAX_15M_CANDLES = 500

# ─── قوانین شبیه‌سازی ───
# 15m → فقط دیتای واقعی (بدون fallback)
# 1h  → دیتای واقعی + شبیه‌سازی از 1D
# 4h  → کاملاً شبیه‌سازی از 1D
# 1D  → خودش

SYNTH_FACTOR: dict[str, int] = {
    "1h": 24,  # 1D → 24×1h
    "4h": 6,  # 1D → 6×4h
}

DAY_SECONDS = 24 * 60 * 60


@dataclass(slots=True)
class GetCandlesWithFallbackUseCase:
    """دریافت کندل با شبیه‌سازی بازه‌های خالی از تایم‌فریم بالاتر."""

    exchange: ExchangePort

    async def execute(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> CandlesWithFallback:
        if limit <= 0 or limit > 3000:
            raise ValueError("limit must be between 1 and 3000")

        if timeframe not in ("15m", "1h", "4h", "1D"):
            raise ValueError(
                f"Unsupported timeframe '{timeframe}'. "
                "Valid: 15m, 1h, 4h, 1D"
            )

        # ─── 1D: مستقیم ───
        if timeframe == "1D":
            candles = await self._fetch(symbol, "D", limit)
            return CandlesWithFallback(
                candles=candles,
                synthetic_ranges=[],
                requested_tf=timeframe,
                applied_limit=limit,
                real_candles_count=len(candles),
                synthetic_candles_count=0,
            )

        # ─── 15m: فقط واقعی، محدود ───
        if timeframe == "15m":
            # والکس "15" رو به عنوان 1m برمی‌گردونه (نه 15m)
            # پس ما 15m رو با 1m شبیه‌سازی نمی‌کنیم — فقط دیتای خام می‌گیریم
            # و بعد با aggregation به 15m تبدیل می‌کنیم
            raw_1m = await self._fetch(symbol, "15", MAX_15M_CANDLES * 15)
            candles = self._aggregate(raw_1m, factor=15)
            if len(candles) > MAX_15M_CANDLES:
                candles = candles[-MAX_15M_CANDLES:]
            return CandlesWithFallback(
                candles=candles,
                synthetic_ranges=[],
                requested_tf=timeframe,
                applied_limit=min(limit, MAX_15M_CANDLES),
                real_candles_count=len(candles),
                synthetic_candles_count=0,
            )

        # ─── 1h / 4h: واقعی + شبیه‌سازی از 1D ───
        return await self._fetch_with_fallback(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    # ────────────────────────────────────────
    #                    Internals
    # ────────────────────────────────────────

    async def _fetch(
        self,
        symbol: str,
        resolution: str,
        limit: int,
    ) -> list[Candle]:
        """دریافت مستقیم از والکس."""
        # ثانیه‌ی هر کندل بر اساس resolution
        # طبق کامنت client.py:
        # "15" = 1m, "60" = 1h, "D" = 1d
        secs_per = {
            "15": 60,         # 1 دقیقه
            "60": 60 * 60,    # 1 ساعت
            "D": 24 * 60 * 60,  # 1 روز
        }[resolution]

        now = int(time.time())
        # حاشیه‌ی ۱۰٪ اضافه
        needed = int(limit * secs_per * 1.1)
        from_ts = now - needed

        try:
            result = await self.exchange.get_candles(
                symbol=symbol,
                resolution=resolution,
                from_ts=from_ts,
                to_ts=now,
            )
            return result
        except Exception as e:
            # لاگ خطا برای debug
            print(f"[_fetch] error {symbol} {resolution}: {e}", flush=True)
            return []

    async def _fetch_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> CandlesWithFallback:
        """1h یا 4h: دیتای واقعی + شبیه‌سازی از 1D."""
        factor = SYNTH_FACTOR[timeframe]
        secs_per = 60 * 60 * (1 if timeframe == "1h" else 4)

        # ─── ۱) دیتای واقعی ───
        # resolution برای 1h = "60"، برای 4h هم "60" (بعداً ادغام می‌کنیم)
        real_candles: list[Candle] = []
        if timeframe == "1h":
            real_candles = await self._fetch(symbol, "60", limit)

        # برای 4h، از 1h می‌گیریم و ادغام می‌کنیم
        if timeframe == "4h":
            raw_1h = await self._fetch(symbol, "60", limit * 4)
            real_candles = self._aggregate(raw_1h, factor=4)

        # ─── ۲) چک کن آیا به limit رسیدیم ───
        if len(real_candles) >= limit:
            return CandlesWithFallback(
                candles=real_candles[-limit:],
                synthetic_ranges=[],
                requested_tf=timeframe,
                applied_limit=limit,
                real_candles_count=len(real_candles),
                synthetic_candles_count=0,
            )

        # ─── ۳) نیاز به شبیه‌سازی از 1D ───
        real_count = len(real_candles)
        missing = limit - real_count

        # چقدر 1D لازم داریم (برای پر کردن missing کندل از TF فعلی)
        days_needed = (missing // factor) + 2  # حاشیه
        daily = await self._fetch(symbol, "D", days_needed)

        if not daily:
            return CandlesWithFallback(
                candles=real_candles,
                synthetic_ranges=[],
                requested_tf=timeframe,
                applied_limit=limit,
                real_candles_count=real_count,
                synthetic_candles_count=0,
            )

        # ─── ۴) شبیه‌سازی ───
        # اگه دیتای واقعی داریم، فقط روزهای قبلش رو بساز
        earliest_real = real_candles[0].time if real_candles else None

        synthetic: list[Candle] = []
        for day in daily:
            # اگه روز، از earliest_real جدیدتره، رد کن
            if earliest_real is not None and day.time >= earliest_real:
                continue
            # آخرین کندل شبیه‌سازی این روز هم نباید از earliest_real رد بشه
            interpolated = self._interpolate_day(day=day, factor=factor)
            if earliest_real is not None:
                interpolated = [
                    c for c in interpolated if c.time < earliest_real
                ]
            synthetic.extend(interpolated)

        # آخرین missing کندل شبیه‌سازی
        synthetic = synthetic[-missing:] if missing > 0 else []

        # ─── ۵) ترکیب با dedup و sort ───
        combined = synthetic + real_candles
        # dedup بر اساس time (اولی که دیدیم رو نگه دار — یعنی synthetic)
        seen = set()
        deduped: list[Candle] = []
        for c in combined:
            if c.time in seen:
                continue
            seen.add(c.time)
            deduped.append(c)
        # sort asc
        deduped.sort(key=lambda c: c.time)
        # آخرین limit
        combined = deduped[-limit:]

        # ─── ۶) synthetic_ranges ───
        ranges: list[SyntheticRange] = []
        if synthetic:
            ranges.append(
                SyntheticRange(
                    from_ts=synthetic[0].time,
                    to_ts=synthetic[-1].time,
                    source_tf="1D",
                )
            )

        return CandlesWithFallback(
            candles=combined,
            synthetic_ranges=ranges,
            requested_tf=timeframe,
            applied_limit=limit,
            real_candles_count=len(real_candles),
            synthetic_candles_count=len(synthetic),
        )

    @staticmethod
    def _aggregate(candles: list[Candle], factor: int) -> list[Candle]:
        """ادغام کندل‌های پایه (مثلاً 1h → 4h)."""
        if factor <= 1 or not candles:
            return candles

        sorted_c = sorted(candles, key=lambda c: c.time)
        result: list[Candle] = []

        for i in range(0, len(sorted_c), factor):
            group = sorted_c[i : i + factor]
            if not group:
                continue
            result.append(
                Candle(
                    time=group[0].time,
                    open=group[0].open,
                    high=max(c.high for c in group),
                    low=min(c.low for c in group),
                    close=group[-1].close,
                    volume=sum((c.volume for c in group), Decimal(0)),
                )
            )
        return result

    @staticmethod
    def _interpolate_day(day: Candle, factor: int) -> list[Candle]:
        """یک کندل 1D رو به `factor` کندل کوچیک‌تر با درون‌یابی خطی تبدیل می‌کنه."""
        o = float(day.open)
        c = float(day.close)
        h = float(day.high)
        l = float(day.low)
        v = float(day.volume)
        secs_per = DAY_SECONDS // factor
        vol_per = v / factor if factor > 0 else 0

        result: list[Candle] = []
        for i in range(factor):
            # قیمت open/close تدریجی از o به c
            t0 = i / factor
            t1 = (i + 1) / factor
            op = o + (c - o) * t0
            cl = o + (c - o) * t1
            # high/low بین این بازه — ساده: همه‌ی روز رو در کندل وسط می‌ذاریم
            # ولی برای طبیعی‌تر، یه نوسان کوچیک اعمال می‌کنیم
            hi = max(op, cl)
            lo = min(op, cl)
            # اگه این کندل، اوج یا کف روز رو پوشش می‌ده، اضافه کن
            if i == factor // 2:
                hi = max(hi, h)
                lo = min(lo, l)

            result.append(
                Candle(
                    time=day.time + i * secs_per,
                    open=Decimal(str(round(op, 8))),
                    high=Decimal(str(round(hi, 8))),
                    low=Decimal(str(round(lo, 8))),
                    close=Decimal(str(round(cl, 8))),
                    volume=Decimal(str(round(vol_per, 8))),
                )
            )
        return result
