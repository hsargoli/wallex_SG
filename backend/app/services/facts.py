"""تولید فکت‌های تحلیلی از کندل‌ها."""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.trend import analyze_trend


@dataclass(slots=True)
class PeriodFacts:
    """فکت‌های یک دوره."""

    period: str  # "1y", "3m", "20d"
    timeframe: str  # "1D", "1h", "15m"
    candles_count: int

    # بازدهی
    change_pct: Decimal
    first_price: Decimal
    last_price: Decimal

    # سقف و کف
    high_price: Decimal
    high_time: int
    low_price: Decimal
    low_time: int

    # نوسان
    volatility_pct: Decimal  # ATR%
    max_drop_pct: Decimal
    max_rise_pct: Decimal
    avg_range_pct: Decimal  # میانگین (high-low)/close در هر کندل
    daily_vol_pct: Decimal  # معادل روزانه (نرمال‌شده)

    # پولبک
    pullback_count: int  # تعداد افت > 5٪
    pullback_avg_pct: Decimal

    # نوسان‌های بزرگ (swings)
    swing_count: int  # تعداد نوسان‌های > 5٪ (صعود یا نزول)
    biggest_rise_pct: Decimal  # بزرگ‌ترین صعود یک کندلی
    biggest_rise_time: int  # زمانش
    biggest_drop_pct_swing: Decimal  # بزرگ‌ترین افت
    biggest_drop_time: int  # زمانش

    # روند
    trend_direction: str  # bullish/bearish/neutral
    trend_strength: str  # weak/medium/strong
    trend_pattern: str  # trending/choppy/ranging
    trend_score: int

    # حجم
    avg_volume: Decimal
    volume_vs_avg: Decimal  # نسبت آخرین به میانگین

    facts: list[str] = field(default_factory=list)
    interpretation: str = ""  # متن قابل‌فهم فارسی


def compute_period_facts(
    candles: list[Candle],
    period: str,
    timeframe: str,
) -> PeriodFacts | None:
    """محاسبه‌ی فکت‌های یک دوره."""
    if not candles or len(candles) < 20:
        return None

    sorted_c = sorted(candles, key=lambda c: c.time)

    # قیمت‌ها
    first = sorted_c[0]
    last = sorted_c[-1]
    first_price = first.close
    last_price = last.close

    if first_price == 0:
        return None

    change_pct = ((last_price - first_price) / first_price) * 100

    # سقف و کف
    high_candle = max(sorted_c, key=lambda c: c.high)
    low_candle = min(sorted_c, key=lambda c: c.low)
    high_price = high_candle.high
    low_price = low_candle.low

    # نوسان — ATR% ساده
    ranges = [(c.high - c.low) / c.close * 100 for c in sorted_c if c.close > 0]
    avg_range_pct = sum(ranges) / len(ranges) if ranges else Decimal(0)

    # نوسان معادل روزانه — نرمال‌سازی بر اساس تایم‌فریم
    # فرض: نوسان تصادفی براونی → factor = √(24 / hours_per_candle)
    TF_HOURS = {"1D": 24, "1h": 1, "15m": 0.25}
    hours = TF_HOURS.get(timeframe, 1)
    if hours > 0:
        from math import sqrt
        factor = sqrt(24 / hours)
        daily_vol_pct = avg_range_pct * Decimal(str(factor))
    else:
        daily_vol_pct = avg_range_pct

    # بیشترین افت/رشد روزانه
    daily_changes = []
    for i in range(1, len(sorted_c)):
        prev = sorted_c[i - 1].close
        curr = sorted_c[i].close
        if prev > 0:
            daily_changes.append(((curr - prev) / prev) * 100)

    max_drop = min(daily_changes) if daily_changes else Decimal(0)
    max_rise = max(daily_changes) if daily_changes else Decimal(0)

    # پولبک — آستانه‌ی متفاوت بر اساس TF
    # 1D: 5٪ | 1h: 2٪ | 15m: 0.5٪
    PB_THRESHOLD = {
        "1D": Decimal(-5),
        "1h": Decimal(-2),
        "15m": Decimal(-0.5),
    }
    threshold = PB_THRESHOLD.get(timeframe, Decimal(-5))
    pullbacks = [d for d in daily_changes if d < threshold]
    pullback_count = len(pullbacks)
    pullback_avg = (
        sum(pullbacks) / len(pullbacks) if pullbacks else Decimal(0)
    )

    # ─── نوسان‌های بزرگ (swings) ───
    # آستانه‌ی نوسان بر اساس TF
    SWING_THRESHOLD = {
        "1D": Decimal(5),
        "1h": Decimal(2),
        "15m": Decimal(0.5),
    }
    swing_th = SWING_THRESHOLD.get(timeframe, Decimal(5))

    # شمارش نوسان‌های مثبت و منفی بالای آستانه
    big_moves = [d for d in daily_changes if abs(d) >= swing_th]
    swing_count = len(big_moves)

    # بزرگ‌ترین صعود و افت با زمان
    biggest_rise_pct = Decimal(0)
    biggest_rise_time = 0
    biggest_drop_pct_swing = Decimal(0)
    biggest_drop_time = 0

    for i in range(1, len(sorted_c)):
        prev = sorted_c[i - 1].close
        curr = sorted_c[i].close
        if prev <= 0:
            continue
        d = ((curr - prev) / prev) * 100
        if d > biggest_rise_pct:
            biggest_rise_pct = d
            biggest_rise_time = sorted_c[i].time
        if d < biggest_drop_pct_swing:
            biggest_drop_pct_swing = d
            biggest_drop_time = sorted_c[i].time

    # روند از analyze_trend
    trend = analyze_trend(sorted_c)

    # حجم — میانگین ۲۴ کندل آخر (نه کل دوره)
    recent = sorted_c[-24:] if len(sorted_c) >= 24 else sorted_c
    recent_vols = [c.volume for c in recent]
    avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else Decimal(0)

    # آخرین حجم = میانگین ۳ کندل آخر (برای کاهش noise)
    last_3 = sorted_c[-3:] if len(sorted_c) >= 3 else sorted_c
    last_vol = sum((c.volume for c in last_3), Decimal(0)) / len(last_3)

    vol_ratio = (last_vol / avg_vol) if avg_vol > 0 else Decimal(0)

    # ─── تولید فکت‌های متنی ───
    facts: list[str] = []

    # ۱. بازدهی
    if change_pct >= Decimal(100):
        facts.append(f"در این دوره {change_pct:.0f}٪ رشد — بازدهی فوق‌العاده")
    elif change_pct >= Decimal(20):
        facts.append(f"در این دوره {change_pct:.1f}٪ رشد داشته")
    elif change_pct >= Decimal(0):
        facts.append(f"در این دوره {change_pct:.1f}٪ رشد ملایم")
    elif change_pct >= Decimal(-20):
        facts.append(f"در این دوره {change_pct:.1f}٪ افت داشته")
    else:
        facts.append(f"در این دوره {change_pct:.1f}٪ افت — عملکرد ضعیف")

    # ۲. موقعیت فعلی نسبت به سقف/کف
    if high_price > 0:
        from_high = ((last_price - high_price) / high_price) * 100
        if from_high >= Decimal(-5):
            facts.append("قیمت فعلی نزدیک سقف تاریخی — احتیاط")
        elif from_high >= Decimal(-20):
            facts.append(f"{abs(from_high):.1f}٪ زیر سقف تاریخی")

    if low_price > 0:
        from_low = ((last_price - low_price) / low_price) * 100
        if from_low >= Decimal(50):
            facts.append(f"{from_low:.0f}٪ بالای کف تاریخی")

    # ۳. پولبک
    if pullback_count > 0:
        facts.append(
            f"{pullback_count} بار پولبک بالای ۵٪ (میانگین {abs(pullback_avg):.1f}٪)"
        )

    # ۴. نوسان
    if daily_vol_pct >= Decimal(8):
        level = "بسیار بالا"
    elif daily_vol_pct >= Decimal(5):
        level = "بالا"
    elif daily_vol_pct >= Decimal(3):
        level = "متوسط"
    elif daily_vol_pct >= Decimal(1.5):
        level = "کم"
    else:
        level = "بسیار کم (آروم)"

    facts.append(
        f"نوسان {level}: {daily_vol_pct:.1f}٪ روزانه "
        f"({avg_range_pct:.2f}٪ در هر کندل)"
    )

    # فکت نوسان‌های بزرگ
    if swing_count > 0:
        import datetime

        def _fmt_date(ts: int) -> str:
            if not ts:
                return "—"
            try:
                d = datetime.datetime.fromtimestamp(ts)
                return d.strftime("%d %b")
            except Exception:
                return "—"

        rise_date = _fmt_date(biggest_rise_time)
        drop_date = _fmt_date(biggest_drop_time)

        parts = [f"{swing_count} نوسان > {swing_th}٪"]
        if biggest_rise_pct > 0:
            parts.append(f"بزرگ‌ترین صعود: +{biggest_rise_pct:.1f}٪ ({rise_date})")
        if biggest_drop_pct_swing < 0:
            parts.append(
                f"بزرگ‌ترین افت: {biggest_drop_pct_swing:.1f}٪ ({drop_date})"
            )
        facts.append(" — ".join(parts))

    # ۵. روند
    direction_fa = {
        "bullish": "صعودی",
        "bearish": "نزولی",
        "neutral": "بی‌طرف",
    }.get(trend.direction, "بی‌طرف")
    strength_fa = {
        "strong": "قوی",
        "medium": "متوسط",
        "weak": "ضعیف",
    }.get(trend.strength, "")
    pattern_fa = {
        "trending": "رونددار",
        "choppy": "پرنوسان",
        "ranging": "بازه‌ای",
    }.get(trend.pattern, "")
    facts.append(f"روند {direction_fa} {strength_fa} — الگوی {pattern_fa}")

    # ۶. حجم — مقایسه با میانگین ۲۴ کندل اخیر
    if vol_ratio >= Decimal(2):
        facts.append(f"حجم {vol_ratio:.1f}x میانگین ۲۴ کندل — فعالیت غیرعادی")
    elif vol_ratio >= Decimal(1.3):
        facts.append(f"حجم {vol_ratio:.1f}x میانگین — بالاتر از معمول")
    elif vol_ratio >= Decimal(0.7):
        facts.append(f"حجم نرمال ({vol_ratio:.1f}x میانگین)")
    elif vol_ratio >= Decimal(0.3):
        facts.append(f"حجم کم ({vol_ratio:.1f}x میانگین)")
    else:
        facts.append(f"حجم بسیار کم ({vol_ratio:.1f}x میانگین)")

    # ۷. بیشترین افت/رشد
    if max_drop < Decimal(-10):
        facts.append(f"بیشترین افت: {max_drop:.1f}٪ در یک کندل")
    if max_rise > Decimal(15):
        facts.append(f"بیشترین رشد: {max_rise:+.1f}٪ در یک کندل")

    # ─── interpretation: متن قابل‌فهم ───
    interp_parts: list[str] = []

    # بازدهی
    if change_pct >= Decimal(50):
        interp_parts.append(f"این ارز در این دوره {change_pct:.0f}٪ رشد کرده — بازدهی چشمگیر")
    elif change_pct >= Decimal(10):
        interp_parts.append(f"این ارز در این دوره {change_pct:.1f}٪ رشد داشته")
    elif change_pct >= Decimal(0):
        interp_parts.append("بازدهی تقریباً صفر — بازار آروم")
    elif change_pct >= Decimal(-10):
        interp_parts.append(f"افت ملایم {change_pct:.1f}٪")
    else:
        interp_parts.append(f"افت شدید {change_pct:.1f}٪ — عملکرد ضعیف")

    # نوسان
    if daily_vol_pct >= Decimal(8):
        interp_parts.append("نوسان بسیار بالا (پرریسک)")
    elif daily_vol_pct >= Decimal(5):
        interp_parts.append("نوسان بالا")
    elif daily_vol_pct >= Decimal(2):
        interp_parts.append("نوسان متوسط")
    else:
        interp_parts.append("نوسان کم")

    # موقعیت نسبت به سقف/کف
    if high_price > 0:
        from_high_pct = ((last_price - high_price) / high_price) * 100
        if from_high_pct >= Decimal(-3):
            interp_parts.append("نزدیک سقف تاریخی")
        elif from_high_pct <= Decimal(-30):
            interp_parts.append("دور از سقف — فضای رشد")

    if low_price > 0:
        from_low_pct = ((last_price - low_price) / low_price) * 100
        if from_low_pct >= Decimal(100):
            interp_parts.append("خیلی بالای کف تاریخی")

    # روند
    dir_fa = {"bullish": "صعودی", "bearish": "نزولی", "neutral": "بی‌طرف"}.get(
        trend.direction, "بی‌طرف"
    )
    interp_parts.append(f"روند فعلی {dir_fa}")

    interpretation = "، ".join(interp_parts) + "."

    return PeriodFacts(
        period=period,
        timeframe=timeframe,
        candles_count=len(sorted_c),
        change_pct=change_pct,
        first_price=first_price,
        last_price=last_price,
        high_price=high_price,
        high_time=high_candle.time,
        low_price=low_price,
        low_time=low_candle.time,
        volatility_pct=trend.volatility_pct,
        max_drop_pct=max_drop,
        max_rise_pct=max_rise,
        avg_range_pct=avg_range_pct,
        daily_vol_pct=daily_vol_pct,
        pullback_count=pullback_count,
        pullback_avg_pct=pullback_avg,
        swing_count=swing_count,
        biggest_rise_pct=biggest_rise_pct,
        biggest_rise_time=biggest_rise_time,
        biggest_drop_pct_swing=biggest_drop_pct_swing,
        biggest_drop_time=biggest_drop_time,
        trend_direction=trend.direction,
        trend_strength=trend.strength,
        trend_pattern=trend.pattern,
        trend_score=trend.score,
        avg_volume=avg_vol,
        volume_vs_avg=vol_ratio,
        facts=facts,
        interpretation=interpretation,
    )



# ────────────────────────────────────────────
#                Overall Summary
# ────────────────────────────────────────────


@dataclass(slots=True)
class OverallSummary:
    """خلاصه‌ی تحلیل کل چهار دوره."""

    overall_behavior: str  # رفتار کلی
    outlook: str  # پیش‌بینی
    risk_level: str  # سطح ریسک
    advice: str  # توصیه
    consistency: str  # هم‌راستایی دوره‌ها


def compute_overall_summary(
    periods: list[PeriodFacts],
) -> OverallSummary:
    """تحلیل مقایسه‌ای چهار دوره."""
    if not periods:
        return OverallSummary(
            overall_behavior="داده کافی نیست",
            outlook="نامشخص",
            risk_level="—",
            advice="—",
            consistency="—",
        )

    # ─── ترتیب: از بلند به کوتاه ───
    order = ["1y", "1mo", "7d", "8h"]
    sorted_p = sorted(
        periods,
        key=lambda x: order.index(x.period) if x.period in order else 99,
    )

    # ─── استخراج شمارنده‌ها ───
    long_term = next((p for p in sorted_p if p.period == "1y"), None)
    short_term = next((p for p in sorted_p if p.period == "8h"), None)
    mid_term = next((p for p in sorted_p if p.period == "1mo"), None)

    # ─── ۱. رفتار کلی ───
    if long_term:
        if long_term.change_pct >= 50 and long_term.pullback_count >= 5:
            behavior = "صعودی قوی با پولبک‌های منظم"
        elif long_term.change_pct >= 20:
            behavior = "صعودی با نوسان"
        elif long_term.change_pct >= 0:
            behavior = "بازه‌ای (range-bound)"
        elif long_term.change_pct >= -20:
            behavior = "نزولی ملایم"
        else:
            behavior = "نزولی قوی"
    else:
        behavior = "نامشخص"

    # ─── ۲. هم‌راستایی دوره‌ها ───
    directions = [
        p.trend_direction for p in sorted_p if p.trend_direction
    ]
    unique_dirs = set(directions)

    if len(unique_dirs) == 1:
        consistency = f"همه‌ی دوره‌ها {list(unique_dirs)[0]}"
        consistent = True
    elif long_term and short_term and long_term.trend_direction == short_term.trend_direction:
        consistency = "دوره‌های بلند و کوتاه هم‌جهت"
        consistent = True
    else:
        consistency = "دوره‌ها متفاوت — احتمال تغییر روند"
        consistent = False

    # ─── ۳. سطح ریسک ───
    if long_term and long_term.daily_vol_pct >= Decimal(8):
        risk = "بالا"
    elif mid_term and mid_term.daily_vol_pct >= Decimal(5):
        risk = "متوسط-بالا"
    elif mid_term and mid_term.daily_vol_pct >= Decimal(3):
        risk = "متوسط"
    else:
        risk = "پایین"

    # ─── ۴. پیش‌بینی (outlook) ───
    if not long_term:
        outlook = "داده کافی نیست"
    elif long_term.trend_direction == "bullish" and consistent:
        if long_term.change_pct >= 100:
            outlook = "احتمال ادامه‌ی صعودی، ولی در سقف — احتیاط"
        else:
            outlook = "احتمال ادامه‌ی روند صعودی"
    elif long_term.trend_direction == "bullish" and not consistent:
        outlook = "روند بلند صعودی ولی کوتاه‌مدت در حال اصلاح"
    elif long_term.trend_direction == "bearish" and consistent:
        outlook = "احتمال ادامه‌ی نزولی"
    elif long_term.trend_direction == "bearish" and not consistent:
        outlook = "نزولی بلندمدت ولی کوتاه‌مدت در حال بهبود"
    else:
        outlook = "روند نامشخص — صبر کن"

    # ─── ۵. توصیه ───
    if not long_term or not short_term:
        advice = "داده کافی نیست"
    elif risk == "بالا":
        advice = "با حد ضرر معامله کن — نوسان بالاست"
    elif long_term.change_pct < 0 and consistent:
        advice = "فعلاً صبر کن تا روند برگرده"
    elif long_term.trend_direction == "bullish" and consistent:
        advice = "فرصت خرید در پولبک‌ها"
    else:
        advice = "با احتیاط معامله کن، منتظر تأیید باش"

    return OverallSummary(
        overall_behavior=behavior,
        outlook=outlook,
        risk_level=risk,
        advice=advice,
        consistency=consistency,
    )
