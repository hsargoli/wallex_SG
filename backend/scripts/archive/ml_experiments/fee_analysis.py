"""تحلیل کارمزد — آیا استراتژی می‌تونه با کارمزد رقابت کنه؟

قاعده‌ی طلایی:
  Win Rate × TP_net > Loss Rate × SL_net
  که net = gross - 0.2%

اگه این برقرار نباشه، حتی با WR بالا ضررده‌ای.
"""

FEE_PCT = 0.2  # کارمزد round trip


def analyze(tp_gross, sl_gross, wr):
    """تحلیل یک ترکیب."""
    tp_net = tp_gross - FEE_PCT
    sl_net = sl_gross + FEE_PCT  # توجه: SL بزرگ‌تر می‌شه چون کارمزد اضافه می‌شه

    # Expected value per trade
    ev = (wr / 100) * tp_net - ((100 - wr) / 100) * sl_net

    # R/R خالص
    rr = tp_net / sl_net if sl_net > 0 else 0

    # حداقل WR برای سر به سر
    # wr × tp_net = (1-wr) × sl_net
    # wr × (tp_net + sl_net) = sl_net
    min_wr = (sl_net / (tp_net + sl_net)) * 100 if (tp_net + sl_net) > 0 else 100

    return {
        "tp_gross": tp_gross,
        "sl_gross": sl_gross,
        "tp_net": tp_net,
        "sl_net": sl_net,
        "wr": wr,
        "ev": ev,
        "rr": rr,
        "min_wr": min_wr,
        "profitable": ev > 0,
    }


def print_analysis(tp, sl, wr):
    r = analyze(tp, sl, wr)
    icon = "✅" if r["profitable"] else "❌"
    print(f"  {icon} TP={tp:.1f}% SL={sl:.1f}% (خالص: +{r['tp_net']:.2f}/-{r['sl_net']:.2f}%)")
    print(f"      R/R خالص: {r['rr']:.2f}  |  حداقل WR: {r['min_wr']:.1f}%  |  WR فعلی: {wr:.1f}%")
    print(f"      EV هر ترید: {r['ev']:+.3f}%")


def main():
    print("="*75)
    print("🧮 تحلیل کارمزد — آیا استراتژی با کارمزد 0.2% سودده است؟")
    print("="*75)
    print()

    # جدول: چه TP/SL با چه WR سودده است؟
    print("📊 سطوح مختلف:")
    print("─" * 75)

    test_wr = 50.0  # فرض: ۵۰٪ win rate

    print(f"\nبا WR = {test_wr}%:")
    for tp in [0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]:
        for sl in [0.5, 0.8, 1.0, 1.5]:
            r = analyze(tp, sl, test_wr)
            icon = "✅" if r["profitable"] else "❌"
            print(f"  {icon} TP={tp:.1f}% SL={sl:.1f}%  |  R/R={r['rr']:.2f}  |  حداقل WR={r['min_wr']:.0f}%  |  EV={r['ev']:+.3f}%")

    print()
    print("="*75)
    print("📊 سوال کلیدی: با WR 60٪ چه ترکیبی سودده است؟")
    print("="*75)

    test_wr = 60.0
    print(f"\nبا WR = {test_wr}%:")
    for tp in [1.0, 1.2, 1.5, 2.0, 2.5, 3.0]:
        for sl in [0.5, 0.8, 1.0, 1.2, 1.5]:
            r = analyze(tp, sl, test_wr)
            if r["profitable"]:
                print(f"  ✅ TP={tp:.1f}% SL={sl:.1f}%  |  EV={r['ev']:+.3f}%")

    print()
    print("="*75)
    print("🎯 نتیجه‌گیری:")
    print("="*75)

    # بهترین ترکیب برای WR های مختلف
    print("\nبرای هر Win Rate، بهترین (TP, SL):")
    print("─"*75)

    candidates = [
        (tp, sl)
        for tp in [1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]
        for sl in [0.5, 0.8, 1.0, 1.2, 1.5]
    ]

    for wr in [40, 45, 50, 55, 60, 65, 70]:
        best = None
        best_ev = -100
        for tp, sl in candidates:
            r = analyze(tp, sl, wr)
            if r["ev"] > best_ev:
                best_ev = r["ev"]
                best = (tp, sl, r)

        if best and best_ev > 0:
            tp, sl, r = best
            print(f"  WR={wr}%  →  TP={tp:.1f}% SL={sl:.1f}%  |  R/R={r['rr']:.2f}  |  EV={r['ev']:+.3f}%  ✅")
        else:
            print(f"  WR={wr}%  →  ❌ هیچ ترکیبی سودده نیست!")

    print()
    print("="*75)
    print("💡 خلاصه:")
    print("="*75)
    print("""
  برای سوددهی با کارمزد 0.2%:
  
  ۱. اگه WR پایین (40-50%) → TP بزرگ لازمه (3%+)
  ۲. اگه WR بالا (60-70%)  → TP کوچیک هم کافیه (1.2-1.5%)
  ۳. SL همیشه باید کوچیک‌تر از TP باشه
  ۴. بهترین ترکیب برای WR~55%:  TP=2.0%, SL=0.8%
""")


if __name__ == "__main__":
    main()
