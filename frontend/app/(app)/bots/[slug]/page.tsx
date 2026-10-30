"use client";

import dynamic from "next/dynamic";

import { use } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Archive,
  Bot,
  Play,
  Square,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Target,
  Wallet,
  Tag,
  Cpu,
  BarChart3,
  Zap,
} from "lucide-react";
import {
  useBot,
  useBotStatus,
  useStartBot,
  useStopBot,
  useResetBot,
} from "@/lib/queries";
import { formatNumber, formatPrice, formatPct } from "@/lib/format";
import { hasUserToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const BotReportsSection = dynamic(
  () => import("@/components/bots/BotReportsSection").then((m) => m.BotReportsSection),
  { loading: () => <Skeleton className="h-40 w-full mt-6" /> },
);

export default function BotDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);

  const info = useBot(slug);
  const status = useBotStatus(slug);
  const startBot = useStartBot();
  const stopBot = useStopBot();
  const resetBot = useResetBot();

  const data = status.data;
  const isRunning = data?.is_running ?? false;
  const ret = data?.total_return_pct ?? 0;
  const profit = data?.profit_tmn ?? 0;
  const isProfit = profit >= 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-4">
        <Link
          href="/bots"
          className="flex h-9 w-9 items-center justify-center rounded-lg border transition hover:border-emerald-500/30 hover:bg-emerald-500/5"
        >
          <ArrowRight className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          {info.isLoading ? (
            <Skeleton className="h-8 w-64" />
          ) : info.data ? (
            <>
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/30 to-emerald-500/0">
                  <Bot className="h-6 w-6 text-emerald-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold tracking-tight">
                    {info.data.name}
                  </h1>
                  <p className="text-xs text-muted-foreground">
                    {info.data.name_en} • v{info.data.version}
                  </p>
                </div>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {info.data.description}
              </p>
            </>
          ) : null}
        </div>

        {/* Controls — per Hosein 2026-10-30: archived → register/view; scheduler → view status */}
        <div className="flex items-center gap-2">
          {info.data?.archived ? (
            hasUserToken() ? (
              <Button
                onClick={() => document.getElementById("paper-section")?.scrollIntoView({ behavior: "smooth" })}
                variant="outline"
                className="gap-2"
              >
                <Archive className="h-4 w-4" />
                مشاهده‌ی آمار (آرشیو)
              </Button>
            ) : (
              <Link href="/register">
                <Button className="gap-2 bg-amber-600 hover:bg-amber-700">
                  ثبت‌نام برای دسترسی (۱۰M)
                </Button>
              </Link>
            )
          ) : (slug === "nooaah" || slug === "sarv_router") ? (
            <Button
              onClick={() => document.getElementById("paper-section")?.scrollIntoView({ behavior: "smooth" })}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              <Activity className="h-4 w-4" />
              مشاهده‌ی وضعیت
            </Button>
          ) : hasUserToken() ? (
            <>
              {!isRunning ? (
                <Button
                  onClick={() => startBot.mutate(slug)}
                  disabled={startBot.isPending}
                  className="gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  <Play className="h-4 w-4" />
                  شروع
                </Button>
              ) : (
                <Button
                  onClick={() => stopBot.mutate(slug)}
                  disabled={stopBot.isPending}
                  variant="destructive"
                  className="gap-2"
                >
                  <Square className="h-4 w-4" />
                  توقف
                </Button>
              )}
              <Button
                onClick={() => resetBot.mutate(slug)}
                variant="outline"
                size="icon"
                disabled={resetBot.isPending || isRunning}
                title="ریست"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Link href="/register">
              <Button className="gap-2 bg-amber-600 hover:bg-amber-700">
                ثبت‌نام برای دسترسی (۱۰M)
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Status banner */}
      <Card
        className={cn(
          "border-2",
          isRunning
            ? "border-emerald-500/40 bg-emerald-500/5"
            : "border-white/10",
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
                  ? `${data.runtime_minutes ?? 0} دقیقه اجرا شده`
                  : "برای شروع، دکمه‌ی شروع را بزنید"}
              </p>
            </div>
          </div>
          {data && (
            <div className="flex items-center gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">نمادهای فعال</p>
                <p className="font-mono font-bold">
                  {data.active_symbols?.length ?? 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">تریدها</p>
                <p className="font-mono font-bold">
                  {data.total_trades ?? 0}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats */}
      {data && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="سرمایه"
            value={`${formatNumber(data.current_capital ?? 0)}`}
            sub={`از ${formatNumber(data.initial_capital ?? 0)} TMN`}
            icon={Wallet}
            accent="text-blue-400"
          />
          <StatCard
            title="سود / زیان"
            value={`${isProfit ? "+" : ""}${formatNumber(profit)}`}
            sub={formatPct(ret)}
            icon={isProfit ? TrendingUp : TrendingDown}
            accent={isProfit ? "text-emerald-400" : "text-red-400"}
          />
          <StatCard
            title="Win Rate"
            value={`${data.win_rate ?? 0}%`}
            sub={`${data.wins ?? 0}W / ${data.losses ?? 0}L`}
            icon={Target}
            accent={
              (data.win_rate ?? 0) >= 55
                ? "text-emerald-400"
                : (data.win_rate ?? 0) >= 45
                  ? "text-amber-400"
                  : "text-red-400"
            }
          />
          <StatCard
            title="Max Drawdown"
            value={`${data.max_drawdown_pct ?? 0}%`}
            sub={`${data.total_trades ?? 0} ترید`}
            icon={Activity}
            accent={
              (data.max_drawdown_pct ?? 0) < 5
                ? "text-emerald-400"
                : (data.max_drawdown_pct ?? 0) < 15
                  ? "text-amber-400"
                  : "text-red-400"
            }
          />
        </div>
      )}

      {/* Info + Active symbols */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Bot info */}
        {info.data && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Cpu className="h-5 w-5 text-emerald-400" />
                اطلاعات ربات
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground">شناسه</p>
                <p className="font-mono text-sm">{info.data.slug}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">نسخه</p>
                <p className="font-mono text-sm">v{info.data.version}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">سازنده</p>
                <p className="text-sm">{info.data.author}</p>
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">
                  <Tag className="mr-1 inline h-3 w-3" />
                  برچسب‌ها
                </p>
                <div className="flex flex-wrap gap-1">
                  {info.data.tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="outline"
                      className="border-blue-500/20 bg-blue-500/5 text-[10px] text-blue-400"
                    >
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs text-muted-foreground">
                  <BarChart3 className="mr-1 inline h-3 w-3" />
                  قابلیت‌ها
                </p>
                <div className="flex flex-wrap gap-1">
                  {info.data.capabilities.map((cap) => (
                    <Badge
                      key={cap}
                      variant="outline"
                      className="border-emerald-500/20 bg-emerald-500/5 text-[10px] text-emerald-400"
                    >
                      {cap}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Active symbols */}
        {data && data.active_symbols && data.active_symbols.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Zap className="h-5 w-5 text-emerald-400" />
                نمادهای فعال
                <Badge variant="outline" className="mr-auto text-[10px]">
                  {data.active_symbols.length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {data.active_symbols.map((sym) => (
                  <div
                    key={sym}
                    className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2"
                  >
                    <span className="font-mono text-xs font-semibold">
                      {sym}
                    </span>
                    <Badge
                      variant="outline"
                      className="border-emerald-500/20 text-[9px] text-emerald-400"
                    >
                      active
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Positions + Trades */}
      {data && (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Open positions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-emerald-400" />
                  پوزیشن‌های باز
                </span>
                <Badge variant="outline">
                  {data.open_positions?.length ?? 0}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!data.open_positions || data.open_positions.length === 0 ? (
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

          {/* Recent trades */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-emerald-400" />
                  آخرین تریدها
                </span>
                <Badge variant="outline">{data.total_trades ?? 0}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!data.recent_trades || data.recent_trades.length === 0 ? (
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
      )}
      <div id="paper-section">
        {info.data && (
          <BotReportsSection data={info.data as any} />
        )}
      </div>
    </div>
  );
}

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
