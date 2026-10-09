"use client";

import { useState } from "react";
import { Target, TrendingUp, TrendingDown, ChevronDown, BookOpen } from "lucide-react";
import { useLevels } from "@/lib/queries";
import { formatPrice } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/info-tip";

export function LevelsPanel({
  symbol,
  timeframe,
  compact = false,
}: {
  symbol: string;
  timeframe: string;
  compact?: boolean;
}) {
  const levels = useLevels(symbol, timeframe);
  const [showPivot, setShowPivot] = useState(true);
  const [showSwings, setShowSwings] = useState(true);
  const [showPivotExplain, setShowPivotExplain] = useState(false);
  const [showSwrExplain, setShowSwrExplain] = useState(false);

  if (levels.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!levels.data) return null;

  const { pivot, swings, current_price } = levels.data;
  const currentPrice = Number(current_price);

  return (
    <div className="space-y-4">
      {/* Pivot Points */}
      {pivot && (
        <Card>
          <CardHeader
            className="flex cursor-pointer flex-row items-center justify-between space-y-0 pb-3"
            onClick={() => setShowPivot((v) => !v)}
          >
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-5 w-5 text-emerald-400" />
              سطوح Pivot Point
              <InfoTip text="سطوح کلاسیک Pivot — R1/R2/R3 مقاومت (سقف)، PP نقطه‌ی محوری، S1/S2/S3 حمایت (کف). قیمت معمولاً بین این سطوح نوسان می‌کند." />
            </CardTitle>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                !showPivot && "-rotate-90",
              )}
            />
          </CardHeader>
          {showPivot && (
            <CardContent>
              {/* Resistance side */}
              <div className="mb-3 space-y-1.5">
                <p className="text-[10px] font-medium text-muted-foreground">
                  مقاومت‌ها
                </p>
                <PivotRow label="R3" value={pivot.r3} current={currentPrice} color="text-red-400" />
                <PivotRow label="R2" value={pivot.r2} current={currentPrice} color="text-red-400" />
                <PivotRow label="R1" value={pivot.r1} current={currentPrice} color="text-red-400" />
              </div>

              {/* PP */}
              <div className="my-3">
                <PivotRow
                  label="PP"
                  value={pivot.pp}
                  current={currentPrice}
                  color="text-amber-400"
                  highlight
                />
              </div>

              {/* Support side */}
              <div className="space-y-1.5">
                <p className="text-[10px] font-medium text-muted-foreground">
                  حمایت‌ها
                </p>
                <PivotRow label="S1" value={pivot.s1} current={currentPrice} color="text-emerald-400" />
                <PivotRow label="S2" value={pivot.s2} current={currentPrice} color="text-emerald-400" />
                <PivotRow label="S3" value={pivot.s3} current={currentPrice} color="text-emerald-400" />
              </div>

              {/* دکمه توضیح */}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowPivotExplain((v) => !v);
                }}
                className={cn(
                  "mt-3 flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed py-2 text-[11px] transition-colors",
                  showPivotExplain
                    ? "border-emerald-500/40 bg-emerald-500/[0.05] text-emerald-400"
                    : "border-border/40 text-muted-foreground hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] hover:text-emerald-400",
                )}
              >
                <BookOpen className="h-3.5 w-3.5" />
                {showPivotExplain ? "بستن توضیحات" : "توضیح کامل این سطوح"}
                <ChevronDown
                  className={cn(
                    "h-3.5 w-3.5 transition-transform",
                    showPivotExplain && "rotate-180",
                  )}
                />
              </button>

              {/* پنل توضیحات Pivot */}
              {showPivotExplain && (
                <div className="mt-3 space-y-3 rounded-lg border border-border/40 bg-background/40 p-4 text-[12px] leading-relaxed text-muted-foreground">
                  <div>
                    <p className="mb-1 text-sm font-bold text-emerald-400">
                      📍 این سطوح چیه؟
                    </p>
                    <p>
                      Pivot Points یک روش کلاسیک تحلیل تکنیکاله که سطوح کلیدی قیمت رو بر اساس
                      سه عدد دوره‌ی قبل (بالاترین قیمت، پایین‌ترین قیمت، قیمت بسته) حساب می‌کنه.
                      این سطوح به سه بخش تقسیم می‌شن:
                    </p>
                  </div>

                  <div className="space-y-2 border-r-2 border-red-500/40 pr-3">
                    <p className="text-sm font-bold text-red-400">
                      🔴 R1 / R2 / R3 (مقاومت‌ها)
                    </p>
                    <p>
                      سه سطح بالای PP. اینا جاهایی‌ان که اگه قیمت بهشون برسه، احتمال
                      برگشت به پایین هست. هرچی R بالاتر، مقاومتش قوی‌تر.
                    </p>
                  </div>

                  <div className="space-y-2 border-r-2 border-amber-500/40 pr-3">
                    <p className="text-sm font-bold text-amber-400">
                      🟡 PP (نقطه‌ی محوری)
                    </p>
                    <p>
                      مرکز همه‌چیز. معیار تشخیص روند:
                    </p>
                    <p className="text-[11px]">
                      • قیمت <b>بالای</b> PP = تمایل صعودی
                      <br />
                      • قیمت <b>زیر</b> PP = تمایل نزولی
                    </p>
                  </div>

                  <div className="space-y-2 border-r-2 border-emerald-500/40 pr-3">
                    <p className="text-sm font-bold text-emerald-400">
                      🟢 S1 / S2 / S3 (حمایت‌ها)
                    </p>
                    <p>
                      سه سطح پایین PP. اگه قیمت بهشون برسه، احتمال برگشت به بالا هست.
                      هرچی S پایین‌تر، حمایتش قوی‌تر.
                    </p>
                  </div>

                  <div className="rounded-md border border-amber-500/20 bg-amber-500/[0.03] p-2.5 text-[11px]">
                    <p className="mb-1 font-bold text-amber-400">⚠️ چطور استفاده کنم؟</p>
                    <p>
                      این سطوح <b>خط قطعی نیستن</b> — فقط جاهایی‌ان که احتمال واکنش قیمت بیشتره.
                      مثلاً اگه قیمت به R1 برسه و نتونه ردش کنه، احتمال افت هست → فرصت فروش.
                      اگه R1 رو بشکنه و بالا بره، ممکنه بره سمت R2.
                    </p>
                  </div>

                  <p className="text-[11px] italic">
                    💡 نکته: در روندهای قوی، قیمت می‌تونه از همه‌ی این سطوح رد بشه. اینا
                    راهنما هستن، نه تضمین.
                  </p>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Swing Levels */}
      {swings.length > 0 && (
        <Card>
          <CardHeader
            className="flex cursor-pointer flex-row items-center justify-between space-y-0 pb-3"
            onClick={() => setShowSwings((v) => !v)}
          >
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              سطوح حمایت و مقاومت
              <Badge variant="outline" className="text-[10px]">
                {swings.length} سطح
              </Badge>
            </CardTitle>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                !showSwings && "-rotate-90",
              )}
            />
          </CardHeader>
          {showSwings && (
            <CardContent>
              <div className="space-y-1.5">
                {swings.map((swing, i) => (
                  <SwingRow key={i} swing={swing} />
                ))}
              </div>

              {/* دکمه توضیح */}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowSwrExplain((v) => !v);
                }}
                className={cn(
                  "mt-3 flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed py-2 text-[11px] transition-colors",
                  showSwrExplain
                    ? "border-emerald-500/40 bg-emerald-500/[0.05] text-emerald-400"
                    : "border-border/40 text-muted-foreground hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] hover:text-emerald-400",
                )}
              >
                <BookOpen className="h-3.5 w-3.5" />
                {showSwrExplain ? "بستن توضیحات" : "توضیح کامل این سطوح"}
                <ChevronDown
                  className={cn(
                    "h-3.5 w-3.5 transition-transform",
                    showSwrExplain && "rotate-180",
                  )}
                />
              </button>

              {/* پنل توضیحات S/R */}
              {showSwrExplain && (
                <div className="mt-3 space-y-3 rounded-lg border border-border/40 bg-background/40 p-4 text-[12px] leading-relaxed text-muted-foreground">
                  <div>
                    <p className="mb-1 text-sm font-bold text-emerald-400">
                      📍 این سطوح چیه؟
                    </p>
                    <p>
                      این سطوح به‌صورت خودکار از <b>نقاط چرخش (swing points)</b> قیمت پیدا می‌شن.
                      یه swing high یعنی جایی که قیمت بالا رفته و برگشته پایین.
                      یه swing low یعنی جایی که قیمت پایین اومده و برگشته بالا.
                    </p>
                  </div>

                  <div>
                    <p className="mb-1 font-bold text-foreground">
                      🔍 چطور پیدا می‌شن؟
                    </p>
                    <p>
                      برای هر کندل، بررسی می‌شه که آیا از ۵ کندل چپ و ۵ کندل راستش بالاتر/پایین‌تر
                      هست یا نه. اگه بله، اون یه swing point هست. بعد سطوح نزدیک به هم
                      (کمتر از ۰.۵٪ فاصله) ادغام می‌شن تا خطوط تمیز دربیان.
                    </p>
                  </div>

                  <div className="space-y-2 border-r-2 border-amber-500/40 pr-3">
                    <p className="text-sm font-bold text-amber-400">
                      📊 قدرت سطوح (Badge)
                    </p>
                    <div className="space-y-1.5 text-[11px]">
                      <p>
                        <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 font-bold text-emerald-400">قوی</span>
                        {" "}= ۴ بار یا بیشتر لمس شده. سطح قابل‌اعتماد.
                      </p>
                      <p>
                        <span className="rounded bg-amber-500/15 px-1.5 py-0.5 font-bold text-amber-400">متوسط</span>
                        {" "}= ۲ یا ۳ بار لمس شده. نسبتاً قابل‌اعتماد.
                      </p>
                      <p>
                        <span className="rounded bg-zinc-500/15 px-1.5 py-0.5 font-bold text-zinc-400">ضعیف</span>
                        {" "}= فقط ۱ بار لمس شده. چندان قابل‌اعتماد نیست.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2 border-r-2 border-emerald-500/40 pr-3">
                    <p className="text-sm font-bold text-emerald-400">
                      💡 «تعداد لمس» چیه؟
                    </p>
                    <p>
                      هر بار که قیمت به یک سطح نزدیک می‌شه، برگشت می‌خوره، و دوباره بهش برمی‌گرده،
                      یک «لمس» حساب می‌شه. هرچی تعداد لمس بیشتر، اون سطح معتبرتره —
                      چون بارها ثابت کرده که قیمت بهش واکنش نشون می‌ده.
                    </p>
                  </div>

                  <div className="rounded-md border border-amber-500/20 bg-amber-500/[0.03] p-2.5 text-[11px]">
                    <p className="mb-1 font-bold text-amber-400">⚠️ چطور استفاده کنم؟</p>
                    <p>
                      وقتی قیمت به یه سطح <b>حمایت</b> نزدیک می‌شه و سطح قویه، فرصت خرید
                      احتمالی. وقتی به یه سطح <b>مقاومت</b> قوی نزدیک می‌شه، فرصت فروش.
                      ولی حتماً با اندیکاتورهای دیگه (RSI، MACD) تأیید کن.
                    </p>
                  </div>

                  <p className="text-[11px] italic">
                    💡 تفاوت با Pivot: Pivot از فرمول ریاضی محاسبه می‌شه، ولی S/R از رفتار واقعی
                    قیمت (نقاط چرخش) استخراج می‌شه. هر دو مکمل همدیگه‌ان.
                  </p>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}

function PivotRow({
  label,
  value,
  current,
  color,
  highlight,
}: {
  label: string;
  value: string;
  current: number;
  color: string;
  highlight?: boolean;
}) {
  const price = Number(value);
  const diffPct = ((current - price) / current) * 100;

  return (
    <div
      className={cn(
        "flex items-center justify-between rounded-lg border px-3 py-2",
        highlight
          ? "border-amber-500/30 bg-amber-500/5"
          : "border-white/5 bg-white/[0.02]",
      )}
    >
      <div className="flex items-center gap-2">
        <span className={cn("font-mono text-xs font-bold", color)}>
          {label}
        </span>
        <span className="font-mono text-sm">{formatPrice(value)}</span>
      </div>
      <span
        className={cn(
          "font-mono text-[10px]",
          diffPct >= 0 ? "text-emerald-400" : "text-red-400",
        )}
      >
        {diffPct >= 0 ? "+" : ""}
        {diffPct.toFixed(2)}%
      </span>
    </div>
  );
}

function SwingRow({
  swing,
}: {
  swing: {
    price: string;
    type: "support" | "resistance";
    touches: number;
    strength: "weak" | "medium" | "strong";
    distance_pct: string;
  };
}) {
  const isSupport = swing.type === "support";
  const Icon = isSupport ? TrendingUp : TrendingDown;
  const color = isSupport ? "text-emerald-400" : "text-red-400";
  const strengthLabel = {
    weak: "ضعیف",
    medium: "متوسط",
    strong: "قوی",
  }[swing.strength];
  const strengthColor = {
    weak: "border-white/10 text-zinc-400",
    medium: "border-amber-500/30 text-amber-400",
    strong: "border-emerald-500/30 text-emerald-400",
  }[swing.strength];

  return (
    <div className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
      <div className="flex items-center gap-3">
        <Icon className={cn("h-4 w-4", color)} />
        <div>
          <p className={cn("font-mono text-sm font-semibold", color)}>
            {formatPrice(swing.price)}
          </p>
          <p className="text-[10px] text-muted-foreground">
            {isSupport ? "حمایت" : "مقاومت"} • {swing.touches} لمس
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={cn("text-[10px]", strengthColor)}>
          {strengthLabel}
        </Badge>
        <span
          className={cn(
            "font-mono text-[10px]",
            Number(swing.distance_pct) >= 0 ? "text-emerald-400" : "text-red-400",
          )}
        >
          {Number(swing.distance_pct) >= 0 ? "+" : ""}
          {Number(swing.distance_pct).toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
