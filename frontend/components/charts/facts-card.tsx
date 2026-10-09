"use client";

import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Calendar,
  AlertTriangle,
  BarChart3,
  Zap,
} from "lucide-react";
import { type PeriodFacts, type FactsSummary } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/info-tip";

interface FactsCardProps {
  periods?: PeriodFacts[];
  summary?: FactsSummary;
  loading?: boolean;
}


const TERM_TIPS = {
  change_pct: "تغییر قیمت از ابتدای این بازه تا الان. مثلاً ۴۱.۳٪- یعنی قیمت در ۱ سال گذشته ۴۱.۳٪ افت داشته.",
  trend: "جهت قیمت در لحظه‌ی فعلی بر اساس ترکیب EMA، MACD و RSI. صعودی = فشار خرید، نزولی = فشار فروش.",
  start_end: "آغاز = قیمت در ابتدای بازه. پایان = قیمت فعلی. مقایسه‌ی این دو، بازدهی دوره رو نشون می‌ده.",
  low_high: "کف = پایین‌ترین قیمت این بازه. سقف = بالاترین قیمت این بازه. فاصله‌ی این دو، دامنه‌ی نوسان کل دوره‌ست.",
  avg_range: "نوسان/کندل = میانگین فاصله‌ی سقف تا کف هر کندل. نوسان/روز = میانگین نوسان روزانه. عدد بالاتر = نوسان بیشتر.",
  pullback: "پولبک = تعداد دفعاتی که قیمت در روند صعودی موقتاً افت کرده و بعد ادامه داده. عدد بالاتر = روند پرنوسان‌تر.",
  volume: "حجم = نسبت حجم معاملات فعلی به میانگین. مثلاً ۲.۳x یعنی حجم ۲.۳ برابر میانگین. بالاتر = علاقه‌ی بیشتر بازار.",
  facts: "این آمار از تحلیل کندل‌های واقعی استخراج شده — نه پیش‌بینی. فقط داده‌ی گذشته رو نشون می‌ده.",
};

const PERIOD_META: Record<
  string,
  { icon: React.ElementType; label: string; sub: string; color: string }
> = {
  "1y": {
    icon: Calendar,
    label: "بلندمدت",
    sub: "۱ سال",
    color: "text-emerald-400",
  },
  "1mo": {
    icon: BarChart3,
    label: "میان‌مدت",
    sub: "۲۹ روز",
    color: "text-blue-400",
  },
  "7d": {
    icon: Activity,
    label: "نوسان هفتگی",
    sub: "۷ روز",
    color: "text-purple-400",
  },
  "8h": {
    icon: Zap,
    label: "لحظه‌ای",
    sub: "۸ ساعت",
    color: "text-amber-400",
  },
};

const DIRECTION_META: Record<
  string,
  { label: string; color: string; icon: React.ElementType }
> = {
  bullish: { label: "صعودی", color: "text-emerald-400", icon: TrendingUp },
  bearish: { label: "نزولی", color: "text-red-400", icon: TrendingDown },
  neutral: { label: "بی‌طرف", color: "text-zinc-400", icon: Minus },
};

function fmtNum(v?: string, digits = 2): string {
  if (!v) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 1_000_000) {
    return (n / 1_000_000).toFixed(2) + "M";
  }
  if (Math.abs(n) >= 1_000) {
    return (n / 1_000).toFixed(2) + "K";
  }
  return n.toLocaleString("en-US", { maximumFractionDigits: digits });
}

function fmtPct(v?: string, digits = 1): string {
  if (!v) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`;
}

export function FactsCard({ periods, summary, loading }: FactsCardProps) {
  if (loading || !periods) {
    return (
      <Card className="border-white/5 bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4 text-emerald-400" />
            فکت‌های تحلیلی
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 w-full rounded-xl" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/5 bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-emerald-400" />
          فکت‌های تحلیلی
          <span className="text-xs font-normal text-muted-foreground">
            — چهار دوره‌ی زمانی
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {periods.map((p) => (
          <PeriodBlock key={p.period} period={p} />
        ))}

        {/* Summary Card */}
        {summary && <SummaryCard summary={summary} />}
      </CardContent>
    </Card>
  );
}

// ────────────────────────────────────────────
//                Summary Card
// ────────────────────────────────────────────

function SummaryCard({ summary }: { summary: FactsSummary }) {
  const riskTone =
    summary.risk_level === "بالا"
      ? "text-red-400 border-red-500/30 bg-red-500/[0.05]"
      : summary.risk_level === "متوسط-بالا"
        ? "text-amber-400 border-amber-500/30 bg-amber-500/[0.05]"
        : summary.risk_level === "متوسط"
          ? "text-blue-400 border-blue-500/30 bg-blue-500/[0.05]"
          : "text-emerald-400 border-emerald-500/30 bg-emerald-500/[0.05]";

  return (
    <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/[0.05] to-transparent p-4">
      {/* Header */}
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15">
          <span className="text-base">🎯</span>
        </div>
        <div>
          <p className="text-sm font-bold">خلاصه و چشم‌انداز</p>
          <p className="text-[10px] text-muted-foreground">
            تحلیل ترکیبی چهار دوره
          </p>
        </div>
      </div>

      {/* Grid 2x2 */}
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        <SummaryItem
          icon="📊"
          label="رفتار کلی"
          value={summary.overall_behavior}
        />
        <SummaryItem
          icon="🔮"
          label="چشم‌انداز"
          value={summary.outlook}
        />
        <SummaryItem
          icon="⚠️"
          label="سطح ریسک"
          value={summary.risk_level}
          valueClass={riskTone}
        />
        <SummaryItem
          icon="💡"
          label="توصیه"
          value={summary.advice}
        />
      </div>

      {/* Consistency */}
      {summary.consistency && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
          <span className="text-xs text-muted-foreground">🔄</span>
          <div>
            <p className="text-[10px] text-muted-foreground">هم‌راستایی دوره‌ها</p>
            <p className="text-xs">{summary.consistency}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryItem({
  icon,
  label,
  value,
  valueClass,
}: {
  icon: string;
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
      <div className="mb-1 flex items-center gap-1.5">
        <span className="text-sm">{icon}</span>
        <span className="text-[10px] text-muted-foreground">{label}</span>
      </div>
      <p className={cn("text-xs font-medium leading-relaxed", valueClass)}>
        {value}
      </p>
    </div>
  );
}

function PeriodBlock({ period }: { period: PeriodFacts }) {
  const meta = PERIOD_META[period.period] || {
    icon: Activity,
    label: period.period,
    sub: period.timeframe,
    color: "text-muted-foreground",
  };
  const Icon = meta.icon;

  if (!period.available) {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Icon className={cn("h-4 w-4", meta.color)} />
          <span className="font-bold">{meta.label}</span>
          <span className="text-xs">({meta.sub})</span>
        </div>
        <p className="mt-2 text-xs text-muted-foreground/60">
          داده‌ای برای این دوره موجود نیست
        </p>
      </div>
    );
  }

  const dir =
    DIRECTION_META[period.trend_direction || "neutral"] || DIRECTION_META.neutral;
  const DirIcon = dir.icon;
  const changeNum = Number(period.change_pct || 0);
  const isUp = changeNum >= 0;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      {/* Header */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon className={cn("h-4 w-4", meta.color)} />
          <span className="text-sm font-bold">{meta.label}</span>
          <span className="text-xs text-muted-foreground">({meta.sub})</span>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[10px]">
          {/* بازدهی دوره */}
          <div
            className="flex items-center gap-1.5"
            title="تغییر قیمت از ابتدای این بازه تا الان"
          >
            <span className="flex items-center gap-1 text-muted-foreground">
              بازدهی دوره:
              <InfoTip text={TERM_TIPS.change_pct} />
            </span>
            <span
              className={cn(
                "flex items-center gap-1 font-mono text-xs font-bold",
                isUp ? "text-emerald-400" : "text-red-400",
              )}
            >
              {isUp ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {fmtPct(period.change_pct)}
            </span>
          </div>

          {/* روند فعلی */}
          <div
            className="flex items-center gap-1.5"
            title="جهت قیمت در لحظه‌ی فعلی بر اساس EMA/MACD/RSI"
          >
            <span className="flex items-center gap-1 text-muted-foreground">
              روند فعلی:
              <InfoTip text={TERM_TIPS.trend} />
            </span>
            <span
              className={cn(
                "flex items-center gap-1 font-mono text-xs font-bold",
                dir.color,
              )}
            >
              <DirIcon className="h-3 w-3" />
              {dir.label}
            </span>
          </div>
        </div>
      </div>

      {/* آمار سریع — ۴ ستون، هر کدوم دو ردیف */}
      <div className="mb-3 grid grid-cols-2 gap-1.5 md:grid-cols-4">
        <PairStat
          topLabel="آغاز"
          topValue={fmtNum(period.first_price)}
          bottomLabel="پایان"
          bottomValue={fmtNum(period.last_price)}
          tone="zinc"
          infoTip={TERM_TIPS.start_end}
        />
        <PairStat
          topLabel="کف"
          topValue={fmtNum(period.low_price)}
          bottomLabel="سقف"
          bottomValue={fmtNum(period.high_price)}
          tone="red"
          infoTip={TERM_TIPS.low_high}
          positionPct={(() => {
            const low = Number(period.low_price || 0);
            const high = Number(period.high_price || 0);
            const last = Number(period.last_price || 0);
            if (high > low && last > 0) {
              return ((last - low) / (high - low)) * 100;
            }
            return null;
          })()}
        />
        <PairStat
          topLabel="نوسان/کندل"
          topValue={
            period.avg_range_pct
              ? `${Number(period.avg_range_pct).toFixed(2)}%`
              : "—"
          }
          bottomLabel="نوسان/روز"
          bottomValue={
            period.daily_vol_pct
              ? `${Number(period.daily_vol_pct).toFixed(2)}%`
              : "—"
          }
          tone="purple"
          infoTip={TERM_TIPS.avg_range}
        />
        <PairStat
          topLabel="پولبک"
          topValue={String(period.pullback_count ?? 0)}
          bottomLabel="حجم"
          bottomValue={
            period.volume_vs_avg
              ? `${Number(period.volume_vs_avg).toFixed(1)}x`
              : "—"
          }
          tone="amber"
          infoTip={TERM_TIPS.volume}
        />
      </div>

      {/* interpretation — متن قابل‌فهم */}
      {period.interpretation && (
        <div className={cn(
          "mb-3 rounded-lg border px-3 py-2 text-xs leading-relaxed",
          "border-white/5 bg-white/[0.02] text-foreground/80",
        )}>
          <span className="font-bold text-muted-foreground">💡 </span>
          {period.interpretation}
        </div>
      )}

      {/* فکت‌ها */}
      {period.facts && period.facts.length > 0 && (
        <ul className="space-y-1.5 text-xs">
          {period.facts.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-muted-foreground">
              <span className={cn("shrink-0", meta.color)}>•</span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      )}

      {/* هشدار (اگه نزدیک سقف بود) */}
      {period.change_pct &&
        Number(period.change_pct) > 100 &&
        period.high_price &&
        period.last_price &&
        Number(period.last_price) / Number(period.high_price) > 0.95 && (
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/[0.05] px-3 py-2 text-[11px] text-amber-300">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>قیمت نزدیک سقف تاریخی — احتمال اصلاح</span>
          </div>
        )}
    </div>
  );
}

const MINI_TONES = {
  emerald: "border-emerald-500/20 bg-emerald-500/[0.03] text-emerald-400",
  red: "border-red-500/20 bg-red-500/[0.03] text-red-400",
  amber: "border-amber-500/20 bg-amber-500/[0.03] text-amber-400",
  purple: "border-purple-500/20 bg-purple-500/[0.03] text-purple-400",
  zinc: "border-white/10 bg-white/[0.02] text-muted-foreground",
} as const;

function PairStat({
  topLabel,
  topValue,
  bottomLabel,
  bottomValue,
  tone,
  infoTip,
  positionPct,
}: {
  topLabel: string;
  topValue: string;
  bottomLabel: string;
  bottomValue: string;
  tone: keyof typeof MINI_TONES;
  infoTip?: string;
  /** موقعیت ۰-۱۰۰ برای نوار افقی (فقط برای کف/سقف) */
  positionPct?: number | null;
}) {
  return (
    <div className={cn("rounded-xl border px-4 py-3", MINI_TONES[tone])}>
      {/* ردیف ۱ */}
      <div className="flex flex-col gap-0.5">
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          {topLabel}
          {infoTip && <InfoTip text={infoTip} />}
        </span>
        <span className="truncate font-mono text-base font-bold">
          {topValue}
        </span>
      </div>

      {/* نوار موقعیت (اختیاری) */}
      {positionPct !== undefined && positionPct !== null && (
        <div className="my-2">
          <div className="h-1 overflow-hidden rounded-full bg-white/10">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                tone === "red" ? "bg-red-500" : tone === "emerald" ? "bg-emerald-500" : "bg-amber-500",
              )}
              style={{ width: `${Math.max(0, Math.min(100, positionPct))}%` }}
            />
          </div>
        </div>
      )}

      {!positionPct && <div className="my-2 border-t border-white/10" />}

      {/* ردیف ۲ */}
      <div className="flex flex-col gap-0.5">
        <span className="text-xs text-muted-foreground">{bottomLabel}</span>
        <span className="truncate font-mono text-base font-bold">
          {bottomValue}
        </span>
      </div>
    </div>
  );
}
