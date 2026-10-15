"use client";

import Link from "next/link";
import { ArrowLeft, Sparkles, Play, Square, RotateCcw, TrendingUp, TrendingDown, Wallet, Target, Activity, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { LiveChart } from "@/components/landing/live-chart";
import { cn } from "@/lib/utils";
import {
  useGuest,
  useGuestPaperV3Status,
  useStartGuestPaperV3,
  useStopGuestPaperV3,
  useResetGuestPaperV3,
} from "@/lib/queries";

const fmt = (n: number | undefined | null, dec: number = 0) =>
  n == null ? "—" : Math.round(n).toLocaleString("fa-IR") + (dec > 0 ? "" : "");

export default function GuestPage() {
  const guest = useGuest();
  const status = useGuestPaperV3Status();
  const startPaper = useStartGuestPaperV3();
  const stopPaper = useStopGuestPaperV3();
  const resetPaper = useResetGuestPaperV3();

  const data = status.data;
  const isRunning = data?.is_running ?? false;
  const capital = data?.capital ?? guest.data?.capital_total ?? 500_000;
  const pnl = data?.total_pnl ?? 0;
  const pnlPct = data?.total_pnl_pct ?? 0;
  const trades = data?.total_trades ?? 0;
  const winRate = data?.win_rate ?? 0;
  const openPositions = data?.open_positions ?? [];
  const isProfit = pnl >= 0;

  return (
    <div className="dark relative min-h-screen overflow-hidden bg-background text-foreground">
      <BackgroundFX />

      {/* ─── Header ─── */}
      <header className="relative z-10 border-b border-violet-500/15">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <Link href="/" className="flex items-center gap-3 transition hover:opacity-80">
            <SarvLogo size={32} />
            <div>
              <p className="text-sm font-semibold">SarvBots</p>
              <p className="text-[10px] text-muted-foreground">رشد پایدار سبز</p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-2 border-violet-500/40 bg-violet-600/10 text-violet-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />
              حالت مهمان
            </Badge>
            <Button asChild size="sm" variant="outline" className="gap-2 border-violet-500/40 hover:bg-violet-600/10">
              <Link href="/">
                <ArrowLeft className="h-3.5 w-3.5" />
                بازگشت
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* ─── Hero ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pt-8 pb-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight lg:text-3xl">
              <Sparkles className="h-6 w-6 text-violet-400" />
              {guest.data ? `خوش آمدی، مهمان` : "در حال آماده‌سازی..."}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              این محیط شبیه‌سازیـه — پول مجازی، بدون ریسک واقعی
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {!isRunning ? (
              <Button
                onClick={() => startPaper.mutate(undefined)}
                disabled={startPaper.isPending || !guest.data}
                className="gap-2 bg-violet-600 hover:bg-violet-500"
              >
                <Play className="h-4 w-4" />
                شروع Paper
              </Button>
            ) : (
              <Button
                onClick={() => stopPaper.mutate()}
                disabled={stopPaper.isPending}
                variant="destructive"
                className="gap-2"
              >
                <Square className="h-4 w-4" />
                توقف
              </Button>
            )}
            <Button
              onClick={() => resetPaper.mutate()}
              disabled={resetPaper.isPending || isRunning}
              variant="outline"
              size="icon"
              title="ریست"
              className="border-violet-500/40 hover:bg-violet-600/10"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* ─── Status Banner ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-4">
        <Card className={cn("border-2", isRunning ? "border-violet-500/40 bg-violet-500/5" : "border-white/10")}>
          <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
            <div className="flex items-center gap-3">
              <div className={cn("h-3 w-3 rounded-full", isRunning ? "animate-pulse bg-emerald-400" : "bg-muted-foreground/40")} />
              <div>
                <p className="font-semibold">{isRunning ? "در حال اجرا" : "متوقف"}</p>
                <p className="text-xs text-muted-foreground">
                  {isRunning ? "ربات هر ۳ دقیقه بازار را چک می‌کند" : "برای شروع، دکمه‌ی شروع را بزن"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">پوزیشن‌های باز</p>
                <p className="font-mono font-bold">{openPositions.length}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">کل تریدها</p>
                <p className="font-mono font-bold">{trades}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ─── KPI Cards ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="سرمایه"
            value={fmt(capital)}
            sub="تومان"
            icon={Wallet}
            accent="text-violet-300"
            loading={guest.isLoading}
          />
          <KpiCard
            title="سود / زیان"
            value={`${isProfit ? "+" : ""}${fmt(pnl)}`}
            sub={`${pnlPct.toFixed(2)}%`}
            icon={isProfit ? TrendingUp : TrendingDown}
            accent={isProfit ? "text-emerald-400" : "text-rose-400"}
            loading={status.isLoading}
          />
          <KpiCard
            title="Win Rate"
            value={`${winRate.toFixed(1)}%`}
            sub={`${trades} ترید`}
            icon={Target}
            accent={winRate >= 55 ? "text-emerald-400" : winRate >= 45 ? "text-amber-400" : "text-rose-400"}
            loading={status.isLoading}
          />
          <KpiCard
            title="Max Drawdown"
            value={`${(data?.max_drawdown_pct ?? 0).toFixed(2)}%`}
            sub={`${openPositions.length} باز`}
            icon={Activity}
            accent="text-fuchsia-400"
            loading={status.isLoading}
          />
        </div>
      </section>

      {/* ─── Chart ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-5 w-5 text-violet-400" />
              چارت زنده
            </CardTitle>
            <Badge variant="outline" className="border-violet-500/30 text-[10px] text-violet-300">
              داده‌ی نمایشی
            </Badge>
          </CardHeader>
          <CardContent className="-mt-12">
            <LiveChart className="w-full" />
          </CardContent>
        </Card>
      </section>

      {/* ─── Positions + Trades ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Positions */}
          <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-violet-400" />
                  پوزیشن‌های باز
                </span>
                <Badge variant="outline">{openPositions.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {openPositions.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
                  {isRunning ? "ربات در حال بررسی..." : "هنوز پوزیشنی باز نشده"}
                </div>
              ) : (
                <div className="space-y-2">
                  {openPositions.map((p: any, i: number) => (
                    <div key={i} className="rounded-lg border border-violet-500/15 bg-background/40 px-3 py-2.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm font-semibold">{p.symbol}</span>
                        <span className="font-mono text-sm">{Math.round(p.entry_price ?? 0).toLocaleString("fa-IR")}</span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground">
                        <span>TP: {Math.round(p.tp ?? 0).toLocaleString("fa-IR")}</span>
                        <span>SL: {Math.round(p.sl ?? 0).toLocaleString("fa-IR")}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Trades */}
          <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-violet-400" />
                  آخرین تریدها
                </span>
                <Badge variant="outline">{trades}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!data?.recent_trades || data.recent_trades.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
                  هنوز تریدی نداشته
                </div>
              ) : (
                <div className="space-y-1.5">
                  {data.recent_trades.slice(0, 8).map((t: any, i: number) => {
                    const isWin = (t.pnl ?? 0) > 0;
                    return (
                      <div
                        key={i}
                        className={cn(
                          "flex items-center justify-between rounded-lg border px-3 py-2",
                          isWin
                            ? "border-emerald-500/20 bg-emerald-500/5"
                            : "border-rose-500/20 bg-rose-500/5",
                        )}
                      >
                        <div className="flex items-center gap-2">
                          {isWin ? (
                            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                          )}
                          <span className="font-mono text-xs font-semibold">{t.symbol}</span>
                          <span className="text-[10px] text-muted-foreground">{t.exit_reason}</span>
                        </div>
                        <span
                          className={cn(
                            "font-mono text-xs font-bold",
                            isWin ? "text-emerald-400" : "text-rose-400",
                          )}
                        >
                          {(t.pnl ?? 0) > 0 ? "+" : ""}
                          {Math.round(t.pnl ?? 0).toLocaleString("fa-IR")}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ─── Disclaimer + CTA ─── */}
      <section className="relative z-10 mx-auto max-w-4xl px-6 pb-12">
        <div className="rounded-xl border border-violet-500/20 bg-violet-500/[0.04] p-5 text-center">
          <p className="text-xs leading-relaxed text-muted-foreground">
            ⚠️ دارایی شما فقط توی این مرورگر ذخیره شده. اگه مرورگر رو پاک کنی یا از حالت
            incognito استفاده کنی، دارایی از دست می‌ره.
            <br />
            برای دسترسی دائمی از همه‌ی دستگاه‌ها،
            <span className="mx-1 font-semibold text-violet-300">ثبت‌نام کن</span>
            (به‌زودی).
          </p>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="relative z-10 border-t border-violet-500/20">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <div className="flex items-center gap-3">
            <SarvLogo size={28} />
            <p className="text-xs text-muted-foreground">SarvBots · حالت مهمان</p>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 SarvBots</p>
        </div>
      </footer>
    </div>
  );
}

function KpiCard({
  title,
  value,
  sub,
  icon: Icon,
  accent,
  loading,
}: {
  title: string;
  value: string;
  sub: string;
  icon: React.ElementType;
  accent: string;
  loading?: boolean;
}) {
  return (
    <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className={cn("h-4 w-4", accent)} />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <>
            <div className={cn("font-mono text-xl font-bold", accent)}>{value}</div>
            <p className="mt-1 font-mono text-[11px] text-muted-foreground">{sub}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
