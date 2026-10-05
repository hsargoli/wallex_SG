"use client";

import { use, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  AlertCircle,
  Shield,
  Target,
  BarChart3,
  Zap,
  CheckCircle2,
  XCircle,
  ArrowUpRight,
} from "lucide-react";
import {
  useIndicators,
  useMultiTfSignals,
  useSignal,
  useLevels,
} from "@/lib/queries";
import {
  type SignalResponse,
  type SignalRule,
  type SignalStrength,
  type MultiTfSignal,
} from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SymbolSwitcher } from "@/components/markets/symbol-switcher";
import { LevelsPanel } from "@/components/signals/levels-panel";
import { LevelsGuide, TradingPlan } from "@/components/signals/trading-plan";
import { SignalsChart } from "@/components/signals/signals-chart";
import { SignalHero } from "@/components/signals/detail/signal-hero";
import { SignalCta } from "@/components/signals/detail/signal-cta";
import { InfoTip } from "@/components/ui/info-tip";
import { cn } from "@/lib/utils";

const TIMEFRAMES = ["15m", "1h", "4h", "1D"];

export default function SignalDetailPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol: symbolParam } = use(params);
  const symbol = symbolParam.toUpperCase();
  const [timeframe, setTimeframe] = useState("1h");

  const signal = useSignal(symbol, timeframe);
  const multi = useMultiTfSignals(symbol);
  const levels = useLevels(symbol, timeframe);
  const indicators = useIndicators(symbol, timeframe, 300);

  return (
    <div className="space-y-5">
      {/* Symbol switcher + TF tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SymbolSwitcher current={symbol} basePath="/signals" suffix="" />
        <div className="flex items-center gap-0.5 rounded-lg border border-border p-0.5">
          {TIMEFRAMES.map((tf) => (
            <Button
              key={tf}
              variant="ghost"
              size="sm"
              onClick={() => setTimeframe(tf)}
              className={cn(
                "h-7 px-2.5 font-mono text-xs",
                timeframe === tf &&
                  "bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/20",
              )}
            >
              {tf}
            </Button>
          ))}
        </div>
      </div>

      {/* Hero Header */}
      <SignalHero
        symbol={symbol}
        timeframe={timeframe}
        signal={signal.data}
        loading={signal.isLoading}
      />

      {/* Chart (compact) + link to full chart */}
      {indicators.data && (
        <div className="relative">
          <SignalsChart
            indicators={indicators.data}
            levels={levels.data}
            height={320}
          />
          <Link
            href={`/markets/${symbol}/chart`}
            className="absolute right-4 top-4 z-10 flex items-center gap-1 rounded-lg border border-white/10 bg-background/80 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur transition hover:border-emerald-500/30 hover:text-emerald-400"
          >
            چارت کامل
            <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
      )}

      {/* Main Signal (Hero Card + SL/TP + Rules) */}
      {signal.isLoading && <Skeleton className="h-96 w-full" />}
      {signal.data && <MainSignal signal={signal.data} />}

      {/* CTA */}
      <SignalCta symbol={symbol} />

      {/* Confluence Summary */}
      <ConfluenceCard
        data={multi.data?.confluence}
        loading={multi.isLoading}
      />

      {/* Timeframe Grid */}
      <div className="grid gap-3 md:grid-cols-4">
        {TIMEFRAMES.map((tf) => (
          <MultiTfCard
            key={tf}
            timeframe={tf}
            data={multi.data?.timeframes[tf]}
            loading={multi.isLoading}
            active={tf === timeframe}
            onClick={() => setTimeframe(tf)}
          />
        ))}
      </div>

      {/* Trading Plan */}
      {levels.data && <TradingPlan data={levels.data} />}

      {/* Guide */}
      <LevelsGuide />

      {/* Key Levels */}
      <div>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          📊 سطوح کلیدی
        </h2>
        <LevelsPanel symbol={symbol} timeframe={timeframe} />
      </div>
    </div>
  );
}
// ==================== Confluence ====================

function ConfluenceCard({
  data,
  loading,
}: {
  data?: {
    status: string;
    label: string;
    buy_count: number;
    sell_count: number;
    hold_count: number;
  };
  loading: boolean;
}) {
  if (loading) return <Skeleton className="h-24 w-full" />;
  if (!data) return null;

  const config = {
    strong_buy: {
      color: "text-emerald-400",
      bg: "bg-emerald-500/10 border-emerald-500/30",
      icon: TrendingUp,
    },
    lean_buy: {
      color: "text-emerald-300",
      bg: "bg-emerald-500/5 border-emerald-500/20",
      icon: TrendingUp,
    },
    strong_sell: {
      color: "text-red-400",
      bg: "bg-red-500/10 border-red-500/30",
      icon: TrendingDown,
    },
    lean_sell: {
      color: "text-red-300",
      bg: "bg-red-500/5 border-red-500/20",
      icon: TrendingDown,
    },
    mixed: {
      color: "text-amber-400",
      bg: "bg-amber-500/10 border-amber-500/30",
      icon: AlertCircle,
    },
    neutral: {
      color: "text-zinc-400",
      bg: "bg-white/5 border-white/10",
      icon: Minus,
    },
  }[data.status] ?? {
    color: "text-zinc-400",
    bg: "bg-white/5 border-white/10",
    icon: Minus,
  };

  const Icon = config.icon;

  return (
    <Card className={cn("border", config.bg)}>
      <CardContent className="flex flex-wrap items-center justify-between gap-4 py-5">
        <div className="flex items-center gap-4">
          <Icon className={cn("h-10 w-10", config.color)} />
          <div>
            <p className="flex items-center gap-1 text-xs text-muted-foreground">
              تأیید متقابل تایم‌فریم
              <InfoTip text="اگه سیگنال در چند تایم‌فریم (15m، 1h، 4h، 1D) هم‌جهت باشه، اطمینان بالاتر می‌ره. مثلاً ۴ از ۴ خرید = سیگنال خیلی قوی." />
            </p>
            <p className={cn("text-lg font-bold", config.color)}>
              {data.label}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="border-emerald-500/30 text-emerald-400"
          >
            🟢 {data.buy_count} خرید
          </Badge>
          <Badge variant="outline" className="border-red-500/30 text-red-400">
            🔴 {data.sell_count} فروش
          </Badge>
          <Badge variant="outline" className="border-zinc-500/30 text-zinc-400">
            ⚪ {data.hold_count} صبر
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// ==================== Multi-TF Card ====================

function MultiTfCard({
  timeframe,
  data,
  loading,
  active,
  onClick,
}: {
  timeframe: string;
  data?: MultiTfSignal;
  loading: boolean;
  active: boolean;
  onClick: () => void;
}) {
  const config = signalConfig(data?.signal);

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 rounded-xl border bg-card p-4 text-right transition",
        active
          ? "border-emerald-500/40 bg-emerald-500/5"
          : "border-white/5 hover:border-white/10",
      )}
    >
      <config.icon className={cn("h-6 w-6", config.color)} />
      <div className="flex-1">
        <p className="font-mono text-xs text-muted-foreground">{timeframe}</p>
        {loading ? (
          <Skeleton className="mt-1 h-5 w-16" />
        ) : (
          <p className={cn("text-sm font-semibold", config.color)}>
            {config.label}
          </p>
        )}
      </div>
      {data?.confidence !== undefined && data.confidence > 0 && (
        <span className="font-mono text-[10px] text-muted-foreground">
          {data.confidence}%
        </span>
      )}
    </button>
  );
}

// ==================== Main Signal ====================

function MainSignal({ signal }: { signal: SignalResponse }) {
  const config = signalConfig(signal.signal);
  const totalScore = signal.buy_score + signal.sell_score;

  return (
    <div className="space-y-4">
      {/* Hero Card */}
      <Card
        className={cn(
          "border-2",
          signal.signal === "buy" && "border-emerald-500/30 bg-emerald-500/5",
          signal.signal === "sell" && "border-red-500/30 bg-red-500/5",
          signal.signal === "hold" && "border-white/10",
        )}
      >
        <CardContent className="py-6">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Signal */}
            <div>
              <p className="text-xs text-muted-foreground">سیگنال</p>
              <div className="mt-2 flex items-center gap-3">
                <config.icon className={cn("h-10 w-10", config.color)} />
                <div>
                  <p className={cn("text-2xl font-bold", config.color)}>
                    {config.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {signal.symbol} • {signal.timeframe}
                  </p>
                </div>
              </div>
            </div>

            {/* Confidence */}
            <div>
              <p className="text-xs text-muted-foreground">اطمینان</p>
              <p className="mt-2 font-mono text-3xl font-bold">
                {signal.confidence}%
              </p>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  className={cn(
                    "h-full transition-all",
                    signal.confidence >= 70
                      ? "bg-emerald-500"
                      : signal.confidence >= 50
                        ? "bg-amber-500"
                        : "bg-red-500",
                  )}
                  style={{ width: `${signal.confidence}%` }}
                />
              </div>
              <p className="mt-1 text-[10px] text-muted-foreground">
                قدرت: {strengthLabel(signal.strength)}
              </p>
            </div>

            {/* Price */}
            <div>
              <p className="text-xs text-muted-foreground">قیمت فعلی</p>
              <p className="mt-2 font-mono text-xl font-bold">
                {formatPrice(signal.current_price)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SL / TP / RR */}
      {(signal.stop_loss || signal.take_profit) && (
        <div className="grid gap-3 md:grid-cols-3">
          <TargetCard
            label="حد ضرر (Stop Loss)"
            value={signal.stop_loss}
            icon={Shield}
            color="text-red-400"
            info="حد ضرر: اگه قیمت به این سطح برسه، پوزیشن به‌طور خودکار بسته می‌شه تا از ضرر بیشتر جلوگیری کنه"
            hint={`فاصله: ${
              signal.stop_loss
                ? (
                    (Math.abs(Number(signal.stop_loss) - Number(signal.current_price)) /
                      Number(signal.current_price)) *
                    100
                  ).toFixed(2)
                : "—"
            }%`}
          />
          <TargetCard
            label="حد سود (Take Profit)"
            value={signal.take_profit}
            icon={Target}
            color="text-emerald-400"
            info="حد سود: اگه قیمت به این سطح برسه، پوزیشن بسته می‌شه و سود شما تأمین می‌شه"
            hint={`فاصله: ${
              signal.take_profit
                ? (
                    (Math.abs(Number(signal.take_profit) - Number(signal.current_price)) /
                      Number(signal.current_price)) *
                    100
                  ).toFixed(2)
                : "—"
            }%`}
          />
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                نسبت ریسک به ریوارد
                <InfoTip text="نسبت ریسک به ریوارد (R/R): به ازای هر ۱ واحد ریسک (فاصله تا حد ضرر)، چند واحد سود (فاصله تا حد سود) انتظار می‌ره. بالاتر = بهتر. مثلاً ۳ یعنی به ازای ۱ ریسک، ۳ سود." />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-mono text-2xl font-bold text-amber-400">
                {signal.risk_reward ? `1 : ${Number(signal.risk_reward).toFixed(1)}` : "—"}
              </p>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {signal.risk_reward && Number(signal.risk_reward) >= 2
                  ? "✅ نسبت عالی (۲ یا بیشتر)"
                  : "⚠️ نسبت پایین"}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Rules Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-base">
              <BarChart3 className="h-5 w-5 text-emerald-400" />
              تجزیه‌ی قوانین
            </span>
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
              >
                🟢 خرید: {signal.buy_score}
              </Badge>
              <Badge
                variant="outline"
                className="border-red-500/30 bg-red-500/10 text-red-400"
              >
                🔴 فروش: {signal.sell_score}
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Score bar */}
          {totalScore > 0 && (
            <div className="mb-4">
              <div className="flex h-3 overflow-hidden rounded-full bg-white/5">
                <div
                  className="bg-emerald-500 transition-all"
                  style={{
                    width: `${(signal.buy_score / totalScore) * 100}%`,
                  }}
                />
                <div
                  className="bg-red-500 transition-all"
                  style={{
                    width: `${(signal.sell_score / totalScore) * 100}%`,
                  }}
                />
              </div>
            </div>
          )}

          <div className="space-y-2">
            {signal.rules.map((rule, i) => (
              <RuleRow key={i} rule={rule} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Indicators Grid */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-5 w-5 text-emerald-400" />
            اندیکاتورها
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {Object.entries(signal.indicators).map(([key, value]) => (
              <IndicatorBox key={key} name={key} value={value} />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function TargetCard({
  label,
  value,
  icon: Icon,
  color,
  hint,
  info,
}: {
  label: string;
  value: string | null;
  icon: React.ElementType;
  color: string;
  hint: string;
  info?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          {label}
          {info && <InfoTip text={info} />}
        </CardTitle>
        <Icon className={cn("h-4 w-4", color)} />
      </CardHeader>
      <CardContent>
        <p className={cn("font-mono text-lg font-bold", color)}>
          {value ? formatPrice(value) : "—"}
        </p>
        <p className="mt-1 text-[10px] text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  );
}

function RuleRow({ rule }: { rule: SignalRule }) {
  const positive = rule.score > 0;
  const negative = rule.score < 0;
  const neutral = rule.score === 0;

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border px-3 py-2.5 transition",
        positive && "border-emerald-500/20 bg-emerald-500/5",
        negative && "border-red-500/20 bg-red-500/5",
        neutral && "border-white/5 bg-white/[0.02]",
      )}
    >
      {rule.passed ? (
        <CheckCircle2
          className={cn(
            "h-4 w-4 flex-shrink-0",
            positive && "text-emerald-400",
            negative && "text-red-400",
            neutral && "text-zinc-500",
          )}
        />
      ) : (
        <XCircle className="h-4 w-4 flex-shrink-0 text-zinc-600" />
      )}
      <div className="flex-1">
        <p className="font-mono text-[10px] text-muted-foreground">{rule.name}</p>
        <p className="text-sm">{rule.reason}</p>
      </div>
      {!neutral && (
        <Badge
          variant="outline"
          className={cn(
            "font-mono",
            positive && "border-emerald-500/30 text-emerald-400",
            negative && "border-red-500/30 text-red-400",
          )}
        >
          {rule.score > 0 ? "+" : ""}
          {rule.score}
        </Badge>
      )}
    </div>
  );
}

function IndicatorBox({ name, value }: { name: string; value: string | null }) {
  const display = (() => {
    if (value === null) return "—";
    const num = Number(value);
    if (!Number.isFinite(num)) return "—";
    if (Math.abs(num) > 1000) return formatPrice(value);
    return num.toFixed(2);
  })();

  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
      <p className="truncate font-mono text-[10px] text-muted-foreground">
        {name}
      </p>
      <p className="mt-0.5 truncate font-mono text-sm">{display}</p>
    </div>
  );
}

// ==================== Helpers ====================

function signalConfig(signal?: string) {
  switch (signal) {
    case "buy":
      return {
        icon: TrendingUp,
        color: "text-emerald-400",
        label: "خرید",
      };
    case "sell":
      return {
        icon: TrendingDown,
        color: "text-red-400",
        label: "فروش",
      };
    case "hold":
      return {
        icon: Minus,
        color: "text-amber-400",
        label: "صبر",
      };
    default:
      return {
        icon: Activity,
        color: "text-zinc-500",
        label: "بدون داده",
      };
  }
}

function strengthLabel(s: SignalStrength): string {
  return { weak: "ضعیف", medium: "متوسط", strong: "قوی" }[s];
}
