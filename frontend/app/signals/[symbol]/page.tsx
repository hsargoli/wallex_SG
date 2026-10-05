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
import { useIndicators, useSignal } from "@/lib/queries";
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
import { SignalHero } from "@/components/signals/detail/signal-hero";
import { SignalCta } from "@/components/signals/detail/signal-cta";
import { SimpleChart } from "@/components/signals/detail/simple-chart";
import { BeginnerGuide } from "@/components/signals/detail/beginner-guide";
import { InfoTip } from "@/components/ui/info-tip";
import { signalConfig, strengthLabel } from "@/components/signals/detail/_helpers";
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

      {/* Chart (simple) + link to full chart */}
      {indicators.data && (
        <div className="relative rounded-xl border border-white/5 bg-card p-2">
          <SimpleChart
            candles={indicators.data.candles}
            height={320}
            loading={indicators.isLoading}
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

      {/* Main Signal (Hero Card + SL/TP) */}
      {signal.isLoading && <Skeleton className="h-96 w-full" />}
      {signal.data && <MainSignal signal={signal.data} />}

      {/* CTA */}
      <SignalCta symbol={symbol} />

      {/* Beginner Guide — آموزش برای تازه‌کارها */}
      {signal.data && (
        <BeginnerGuide
          reasons={signal.data.reasons}
          signalType={signal.data.signal as "buy" | "sell" | "hold"}
        />
      )}

    </div>
  );
}
// ==================== Confluence ====================

// ==================== Multi-TF Card ====================

// ==================== Main Signal ====================

function MainSignal({ signal }: { signal: SignalResponse }) {
  const config = signalConfig(signal.signal);

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

// ==================== Helpers ====================

