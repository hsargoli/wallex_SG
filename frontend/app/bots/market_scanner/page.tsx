"use client";

import Link from "next/link";
import {
  ArrowRight,
  Search,
  Play,
  Square,
  RotateCcw,
  Activity,
  Clock,
  TrendingUp,
  Zap,
  BarChart3,
  RefreshCw,
} from "lucide-react";
import {
  useBot,
  useBotStatus,
  useStartBot,
  useStopBot,
  useResetBot,
  useSetBotTimeframe,
} from "@/lib/queries";
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

type ScanResult = {
  symbol: string;
  score: number;
  atr_pct: number;
  volume_ratio: number;
  price: string;
  error?: string;
};

export default function MarketScannerPage() {
  const slug = "market_scanner";

  const info = useBot(slug);
  const status = useBotStatus(slug);
  const startBot = useStartBot();
  const stopBot = useStopBot();
  const resetBot = useResetBot();
  const setTimeframe = useSetBotTimeframe();

  const data = status.data;
  const isRunning = data?.is_running ?? false;
  const results: ScanResult[] = data?.results ?? [];

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
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/30 to-blue-500/0">
                  <Search className="h-6 w-6 text-blue-400" />
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

        {/* Controls */}
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <Button
              onClick={() => startBot.mutate(slug)}
              disabled={startBot.isPending}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              <Play className="h-4 w-4" />
              شروع اسکن
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
                {isRunning ? "در حال اسکن" : "متوقف"}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRunning && data
                  ? "اسکن خودکار فعال"
                  : "برای شروع، دکمه‌ی شروع را بزنید"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 text-blue-400">
              <RefreshCw className="h-3 w-3" />
              هر {data?.config?.scan_interval_sec ?? 300} ثانیه
            </Badge>
            <select
              value={data?.config?.timeframe ?? "1h"}
              onChange={(e) => setTimeframe.mutate({ slug, timeframe: e.target.value })}
              disabled={setTimeframe.isPending}
              className="bg-black/40 border border-white/10 rounded px-3 py-1.5 text-sm outline-none focus:border-blue-500 min-w-[100px]"
            >
              {(data?.config?.available_timeframes ?? ["15m", "1h", "4h", "1D"]).map((tf) => (
                <option key={tf} value={tf} className="bg-slate-900">
                  {tf === "15m" ? "۱۵ دقیقه" : tf === "1h" ? "۱ ساعته" : tf === "4h" ? "۴ ساعته" : tf === "1D" ? "روزانه" : tf}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      {data && (
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard
            title="تعداد اسکن"
            value={String(data.scan_count ?? 0)}
            sub="اجرا شده"
            icon={BarChart3}
            accent="text-blue-400"
          />
          <StatCard
            title="نمادهای شناسایی‌شده"
            value={String(data.results_count ?? 0)}
            sub="در آخرین اسکن"
            icon={Zap}
            accent="text-amber-400"
          />
          <StatCard
            title="آخرین اسکن"
            value={
              data.last_scan_at
                ? new Date(data.last_scan_at * 1000).toLocaleTimeString("fa-IR")
                : "—"
            }
            sub={data.started_at ? "شروع: " + new Date(data.started_at * 1000).toLocaleTimeString("fa-IR") : ""}
            icon={Clock}
            accent="text-emerald-400"
          />
        </div>
      )}

      {/* Results table */}
      {data && results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-base">
              <span className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                نمادهای نوسانی
              </span>
              <Badge variant="outline">{results.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-right">
                    <th className="pb-2 font-medium text-muted-foreground">#</th>
                    <th className="pb-2 font-medium text-muted-foreground">نماد</th>
                    <th className="pb-2 font-medium text-muted-foreground">Score</th>
                    <th className="pb-2 font-medium text-muted-foreground">ATR%</th>
                    <th className="pb-2 font-medium text-muted-foreground">Volume</th>
                    <th className="pb-2 font-medium text-muted-foreground">قیمت</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => {
                    if (r.error) {
                      return (
                        <tr key={i} className="border-b border-white/5">
                          <td colSpan={6} className="py-2 text-center text-xs text-red-400">
                            {r.error}
                          </td>
                        </tr>
                      );
                    }
                    return (
                      <tr
                        key={r.symbol}
                        className="border-b border-white/5 transition hover:bg-white/[0.02]"
                      >
                        <td className="py-2 font-mono text-xs text-muted-foreground">
                          {i + 1}
                        </td>
                        <td className="py-2 font-mono text-xs font-semibold">
                          {r.symbol}
                        </td>
                        <td className="py-2">
                          <Badge
                            variant="outline"
                            className={cn(
                              "font-mono text-[10px]",
                              r.score >= 60
                                ? "border-emerald-500/30 text-emerald-400"
                                : r.score >= 40
                                  ? "border-amber-500/30 text-amber-400"
                                  : "border-white/10 text-muted-foreground",
                            )}
                          >
                            {r.score.toFixed(2)}
                          </Badge>
                        </td>
                        <td className="py-2 font-mono text-xs">
                          {r.atr_pct.toFixed(3)}%
                        </td>
                        <td className="py-2 font-mono text-xs text-muted-foreground">
                          {r.volume_ratio.toFixed(2)}
                        </td>
                        <td className="py-2 font-mono text-xs text-muted-foreground">
                          {r.price}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {data && results.length === 0 && !isRunning && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="mx-auto mb-3 h-10 w-10 opacity-20" />
            <p className="text-sm text-muted-foreground">
              برای دیدن نتایج، دکمه‌ی شروع را بزنید
            </p>
          </CardContent>
        </Card>
      )}
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
