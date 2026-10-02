"use client";

import { useState } from "react";
import {
  Play,
  Square,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Target,
  Zap,
  Wallet,
  Sparkles,
} from "lucide-react";
import {
  usePaperV2Status,
  useStartPaperV2,
  useStopPaperV2,
  useResetPaperV2,
} from "@/lib/queries";
import { runSimulation, SimulationResult } from "@/lib/api";
import { formatNumber, formatPrice, formatPct } from "@/lib/format";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function PaperTradingPage() {
  const status = usePaperV2Status();
  const startBot = useStartPaperV2();
  const stopBot = useStopPaperV2();
  const resetBot = useResetPaperV2();

  // Simulation State
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);

  const handleRunSimulation = async () => {
    try {
      setSimLoading(true);
      const res = await runSimulation("2026-09-01", "2026-09-03");
      setSimResult(res);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setSimLoading(false);
    }
  };

  const data = status.data;
  const isRunning = data?.is_running ?? false;
  const profit = data?.profit_tmn ?? 0;
  const ret = data?.total_return_pct ?? 0;
  const isProfit = profit >= 0;

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Zap className="h-6 w-6 text-emerald-400" />
            Paper Trading & Simulator
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            تست زنده استراتژی و شبیه‌سازی گذشته بازار
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isRunning ? (
            <Button
              onClick={() => startBot.mutate()}
              disabled={startBot.isPending}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              <Play className="h-4 w-4" />
              شروع
            </Button>
          ) : (
            <Button
              onClick={() => stopBot.mutate()}
              disabled={stopBot.isPending}
              variant="destructive"
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              توقف
            </Button>
          )}
          <Button
            onClick={() => resetBot.mutate()}
            variant="outline"
            size="icon"
            disabled={resetBot.isPending || isRunning}
            title="ریست"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Simulator Section */}
      <Card className="border-emerald-500/30 bg-emerald-500/5">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-5 w-5 text-amber-400" />
            موتور شبیه‌سازی (ماشین زمان)
          </CardTitle>
          <Button
            onClick={handleRunSimulation}
            disabled={simLoading}
            size="sm"
            className="gap-2 bg-amber-600 hover:bg-amber-700 text-white"
          >
            {simLoading ? "در حال محاسبه..." : "اجرای تست دیتای گذشته"}
          </Button>
        </CardHeader>
        <CardContent>
          {simResult ? (
            <div className="flex items-center justify-between rounded-lg border border-white/10 bg-black/20 p-4">
              <div>
                <p className="text-xs text-muted-foreground">وضعیت اجرای شبیه‌ساز</p>
                <p className="font-mono text-sm font-bold text-emerald-400">
                  {simResult.status.toUpperCase()}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">موجودی نهایی</p>
                <p className="font-mono text-sm font-bold">
                  {formatNumber(simResult.pnl_report.final_balance)} USDT
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">سود / زیان کل (PnL)</p>
                <p
                  className={cn(
                    "font-mono text-sm font-bold",
                    simResult.pnl_report.total_pnl >= 0
                      ? "text-emerald-400"
                      : "text-red-400"
                  )}
                >
                  {simResult.pnl_report.total_pnl >= 0 ? "+" : ""}
                  {formatNumber(simResult.pnl_report.total_pnl)} USDT
                </p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              برای تست الگوریتم روی داده‌های شبیه‌سازی شده، روی دکمه اجرای تست کلیک کنید.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Status banner */}
      <Card
        className={cn(
          "border-2",
          isRunning ? "border-emerald-500/40 bg-emerald-500/5" : "border-white/10",
        )}
      >
        <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "h-3 w-3 rounded-full",
                isRunning ? "animate-pulse bg-emerald-400" : "bg-red-500",
              )}
            />
            <div>
              <p className="font-semibold">
                {isRunning ? "در حال اجرا" : "متوقف"}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRunning && data
                  ? `${data.runtime_minutes} دقیقه اجرا شده`
                  : "برای شروع، دکمه‌ی شروع را بزنید"}
              </p>
            </div>
          </div>
          {data && (
            <div className="flex items-center gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">نمادهای فعال</p>
                <p className="font-mono font-bold">{data.active_symbols.length}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">آخرین بررسی</p>
                <p className="font-mono text-xs">
                  {data.last_check_time
                    ? new Date(data.last_check_time * 1000).toLocaleTimeString(
                        "fa-IR",
                      )
                    : "—"}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Grid */}
      {status.isLoading && !data ? (
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="سرمایه فعلی"
              value={`${formatNumber(data.current_capital)} TMN`}
              sub={`از ${formatNumber(data.initial_capital)}`}
              icon={Wallet}
              accent="text-blue-400"
            />
            <StatCard
              title="سود / زیان"
              value={`${isProfit ? "+" : ""}${formatNumber(profit)} TMN`}
              sub={formatPct(ret)}
              icon={isProfit ? TrendingUp : TrendingDown}
              accent={isProfit ? "text-emerald-400" : "text-red-400"}
            />
            <StatCard
              title="Win Rate"
              value={`${data.win_rate}%`}
              sub={`${data.wins}W / ${data.losses}L`}
              icon={Target}
              accent={
                data.win_rate >= 55
                  ? "text-emerald-400"
                  : data.win_rate >= 45
                    ? "text-amber-400"
                    : "text-red-400"
              }
            />
            <StatCard
              title="Max Drawdown"
              value={`${data.max_drawdown_pct}%`}
              sub={`${data.total_trades} ترید`}
              icon={Activity}
              accent={
                data.max_drawdown_pct < 5
                  ? "text-emerald-400"
                  : data.max_drawdown_pct < 15
                    ? "text-amber-400"
                    : "text-red-400"
              }
            />
          </div>

          {/* Equity Chart */}
          {data.equity_curve.length > 1 && (
            <EquityChart points={data.equity_curve} initial={data.initial_capital} />
          )}

          {/* Two columns */}
          <div className="grid gap-4 lg:grid-cols-2">
            {/* Open Positions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-base">
                    <Activity className="h-5 w-5 text-emerald-400" />
                    پوزیشن‌های باز
                  </span>
                  <Badge variant="outline">
                    {data.open_positions.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.open_positions.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
                    هنوز پوزیشنی باز نشده
                  </div>
                ) : (
                  <div className="space-y-2">
                    {data.open_positions.map((p, i) => (
                      <div
                        key={i}
                        className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm font-semibold">
                              {p.symbol}
                            </span>
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-[10px]",
                                p.strategy === "bounce"
                                  ? "border-purple-500/30 text-purple-400"
                                  : "border-blue-500/30 text-blue-400",
                              )}
                            >
                              {p.strategy}
                            </Badge>
                          </div>
                          <span className="font-mono text-sm">
                            {formatPrice(p.entry_price)}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground">
                          <span>TP: {formatPrice(p.tp)}</span>
                          <span>SL: {formatPrice(p.sl)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Trades */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-base">
                    <TrendingUp className="h-5 w-5 text-emerald-400" />
                    آخرین تریدها
                  </span>
                  <Badge variant="outline">{data.total_trades}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.recent_trades.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
                    هنوز تریدی نداشته
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {data.recent_trades.slice(0, 8).map((t, i) => {
                      const isWin = t.pnl_pct > 0;
                      return (
                        <div
                          key={i}
                          className={cn(
                            "flex items-center justify-between rounded-lg border px-3 py-2",
                            isWin
                              ? "border-emerald-500/20 bg-emerald-500/5"
                              : "border-red-500/20 bg-red-500/5",
                          )}
                        >
                          <div className="flex items-center gap-2">
                            {isWin ? (
                              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                            ) : (
                              <TrendingDown className="h-3.5 w-3.5 text-red-400" />
                            )}
                            <span className="font-mono text-xs font-semibold">
                              {t.symbol}
                            </span>
                            <span className="text-[10px] text-muted-foreground">
                              {t.exit_reason}
                            </span>
                          </div>
                          <div className="text-right">
                            <p
                              className={cn(
                                "font-mono text-xs font-bold",
                                isWin ? "text-emerald-400" : "text-red-400",
                              )}
                            >
                              {t.pnl_pct > 0 ? "+" : ""}
                              {t.pnl_pct.toFixed(2)}%
                            </p>
                            <p className="font-mono text-[10px] text-muted-foreground">
                              {t.pnl_tmn > 0 ? "+" : ""}
                              {formatNumber(t.pnl_tmn)} TMN
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}

// ==================== Sub-components ====================

function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  accent,
}: {
  title: string;
  value: string;
  sub: string;
  icon: React.ElementType;
  accent: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className={cn("h-4 w-4", accent)} />
      </CardHeader>
      <CardContent>
        <div className={cn("font-mono text-xl font-bold", accent)}>{value}</div>
        <p className="mt-1 font-mono text-[11px] text-muted-foreground">{sub}</p>
      </CardContent>
    </Card>
  );
}

function EquityChart({
  points,
  initial,
}: {
  points: { time: number; capital: number }[];
  initial: number;
}) {
  if (points.length < 2) return null;

  const caps = points.map((p) => p.capital);
  const minC = Math.min(...caps, initial);
  const maxC = Math.max(...caps, initial);
  const range = maxC - minC || 1;
  const w = 800;
  const h = 120;

  const polyline = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * w;
      const y = h - ((p.capital - minC) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");

  const initialY = h - ((initial - minC) / range) * h;
  const isUp = caps[caps.length - 1] >= initial;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">نمودار سرمایه</CardTitle>
      </CardHeader>
      <CardContent>
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
          <line
            x1="0"
            y1={initialY}
            x2={w}
            y2={initialY}
            stroke="#71717a"
            strokeWidth="1"
            strokeDasharray="4,4"
          />
          <polyline
            points={polyline}
            fill="none"
            stroke={isUp ? "#10b981" : "#ef4444"}
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
      </CardContent>
    </Card>
  );
}
