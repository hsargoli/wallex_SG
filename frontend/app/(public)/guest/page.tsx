"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Sparkles,
  Play,
  Square,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Wallet,
  Target,
  Activity,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { BackgroundFX } from "@/components/landing/background-fx";
import { GuestSignals } from "@/components/guest/guest-signals";
import { GuestScanner } from "@/components/guest/guest-scanner";
import { GuestPersonality } from "@/components/guest/guest-personality";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { UserBadge } from "@/components/layout/user-badge";
import { cn } from "@/lib/utils";
import { SYMBOLS } from "@/components/paper-trading/symbols";
import { fmt, fmtNum, parseNum, formatNum } from "@/lib/paper-format";
import { PaperStatusBanner } from "@/components/paper-trading/paper-status-banner";
import { PaperDisclaimer } from "@/components/paper-trading/paper-disclaimer";
import { ManualOrderForm } from "@/components/paper-trading/manual-order-form";
import {
  useGuest,
  useGuestPaperV3Status,
  useStartGuestPaperV3,
  useStopGuestPaperV3,
  useResetGuestPaperV3,
  useUserPaperV3Status,
  useStartUserPaperV3,
  useStopUserPaperV3,
  useResetUserPaperV3,
  usePlaceUserOrder,
  useCloseUserPosition,
  useCandlesV2,
  usePlaceGuestOrder,
  useCloseGuestPosition,
  useGuestPrice,
  useMe,
} from "@/lib/queries";
import { getUserToken } from "@/lib/auth";
import { CandlestickChart } from "@/components/charts/candlestick-chart";

export default function GuestPage() {
  const [symbol, setSymbol] = useState<string>("BTCTMN");
  const [timeframe, setTimeframe] = useState<string>("1h");

  // فرم سفارش دستی
  const [orderSymbol, setOrderSymbol] = useState<string>("BTCTMN");
  const [orderAmount, setOrderAmount] = useState<string>("100000");
  const [orderTp, setOrderTp] = useState<string>("2");
  const [orderSl, setOrderSl] = useState<string>("1");
  const [orderLimitPrice, setOrderLimitPrice] = useState<string>("");

  const [isUser, setIsUser] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const userToken = getUserToken();
    setIsUser(!!userToken);
    if (userToken) {
      router.replace("/paper-trading/manual");
    }
  }, [router]);

  const me = useMe();
  const guest = useGuest();
  const guestStatus = useGuestPaperV3Status();
  const userStatus = useUserPaperV3Status();
  const status = isUser ? userStatus : guestStatus;
  const candles = useCandlesV2(symbol, timeframe, 200);
  const guestStart = useStartGuestPaperV3();
  const guestStop = useStopGuestPaperV3();
  const guestReset = useResetGuestPaperV3();
  const userStart = useStartUserPaperV3();
  const userStop = useStopUserPaperV3();
  const userReset = useResetUserPaperV3();
  const startPaper = isUser ? userStart : guestStart;
  const stopPaper = isUser ? userStop : guestStop;
  const resetPaper = isUser ? userReset : guestReset;
  const guestPlace = usePlaceGuestOrder();
  const guestClose = useCloseGuestPosition();
  const userPlace = usePlaceUserOrder();
  const userClose = useCloseUserPosition();
  const placeOrder = isUser ? userPlace : guestPlace;
  const closePosition = isUser ? userClose : guestClose;
  const marketPrice = useGuestPrice(orderSymbol, true);

  // auto-fill قیمت پیشنهادی با قیمت بازار
  useEffect(() => {
    if (marketPrice.data?.price) {
      setOrderLimitPrice(formatNum(String(Math.round(marketPrice.data.price))));
    }
  }, [orderSymbol, marketPrice.data?.price]);

  const data = status.data as
    | {
        is_running?: boolean;
        capital?: number;
        equity?: number;
        total_pnl?: number;
        total_pnl_pct?: number;
        win_rate?: number;
        max_drawdown_pct?: number;
        open_positions?: Array<{
          symbol: string;
          side: string;
          entry_price: number;
          current_price?: number;
          tp?: number;
          sl?: number;
        }>;
        recent_trades?: Array<{
          symbol: string;
          side: string;
          entry_price: number;
          exit_price?: number;
          exit_reason?: string;
          pnl?: number;
          pnl_pct?: number;
        }>;
      }
    | undefined;

  const isRunning = data?.is_running ?? false;
  const capital = data?.capital ?? (guest.data as any)?.capital_total ?? 100_000;
  const pnl = data?.total_pnl ?? 0;
  const pnlPct = data?.total_pnl_pct ?? 0;
  const trades = (data?.recent_trades ?? []).length;
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

          <div className="flex items-center gap-3">
            <UserBadge />
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
              {isUser
                ? `خوش آمدی، ${(me.data as any)?.email?.split("@")[0] ?? "کاربر"}`
                : guest.data
                  ? "خوش آمدی، مهمان"
                  : "در حال آماده‌سازی..."}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              این محیط شبیه‌سازیـه — پول مجازی، بدون ریسک واقعی
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {!isRunning ? (
              <Button
                onClick={() => startPaper.mutate(undefined)}
                disabled={startPaper.isPending || (isUser ? !me.data : !guest.data)}
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

      {/* ─── Status Banner (shared) ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-4">
        <PaperStatusBanner
          isRunning={isRunning}
          openPositionsCount={openPositions.length}
          tradesCount={trades}
          variant="guest"
        />
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
            sub={`${fmtNum(pnlPct, 2)}٪`}
            icon={isProfit ? TrendingUp : TrendingDown}
            accent={isProfit ? "text-emerald-400" : "text-rose-400"}
            loading={status.isLoading}
          />
          <KpiCard
            title="Win Rate"
            value={`${fmtNum(winRate, 1)}٪`}
            sub={`${trades} ترید`}
            icon={Target}
            accent={winRate >= 55 ? "text-emerald-400" : winRate >= 45 ? "text-amber-400" : "text-rose-400"}
            loading={status.isLoading}
          />
          <KpiCard
            title="Max Drawdown"
            value={`${fmtNum(data?.max_drawdown_pct ?? 0, 2)}٪`}
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
              چارت {SYMBOLS.find((s) => s.key === symbol)?.fa ?? symbol}
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 rounded-full border border-violet-500/30 bg-background/50 p-0.5">
                {(["15m", "1h", "4h", "1D"] as const).map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={cn(
                      "rounded-full px-2.5 py-0.5 text-[10px] font-medium transition",
                      tf === timeframe
                        ? "bg-violet-600 text-white"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                    type="button"
                  >
                    {tf}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1 rounded-full border border-violet-500/30 bg-background/50 p-0.5">
                {SYMBOLS.map((s) => (
                  <button
                    key={s.key}
                    onClick={() => setSymbol(s.key)}
                    className={cn(
                      "rounded-full px-2.5 py-0.5 text-[10px] font-medium transition",
                      s.key === symbol
                        ? "bg-violet-600 text-white shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                    type="button"
                  >
                    {s.fa}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {candles.isLoading ? (
              <Skeleton className="h-[400px] w-full" />
            ) : candles.isError || !candles.data?.candles?.length ? (
              <div className="flex h-[400px] items-center justify-center text-sm text-muted-foreground">
                داده‌ای برای نمایش نیست
              </div>
            ) : (
              <CandlestickChart candles={candles.data.candles} />
            )}
          </CardContent>
        </Card>
      </section>

      {/* ─── Guest-only: Signals + Scanner + Personality ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <div className="grid gap-4 lg:grid-cols-3">
          <GuestSignals symbol={symbol} timeframe={timeframe} />
          <GuestScanner />
          <GuestPersonality symbol={symbol} timeframe={timeframe} />
        </div>
      </section>

      {/* ─── Form + Disclaimer (shared) ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_1.5fr]">
          <PaperDisclaimer variant="guest" />
          <ManualOrderForm
            isRunning={isRunning}
            capital={capital}
            openPositionsCount={openPositions.length}
            marketPrice={marketPrice}
            orderSymbol={orderSymbol}
            orderAmount={orderAmount}
            orderTp={orderTp}
            orderSl={orderSl}
            orderLimitPrice={orderLimitPrice}
            setOrderSymbol={setOrderSymbol}
            setOrderAmount={setOrderAmount}
            setOrderTp={setOrderTp}
            setOrderSl={setOrderSl}
            setOrderLimitPrice={setOrderLimitPrice}
            onSubmit={() =>
              placeOrder.mutate({
                side: "buy",
                symbol: orderSymbol,
                amount_tmn: parseFloat(parseNum(orderAmount)) || 0,
                limit_price: parseFloat(parseNum(orderLimitPrice)) || 0,
                tp_pct: parseFloat(orderTp) || 2,
                sl_pct: parseFloat(orderSl) || 1,
              })
            }
            isSubmitting={placeOrder.isPending}
            variant="guest"
          />
        </div>
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
                  {openPositions.map((p: any, i: number) => {
                    const isBuy = p.side === "buy";
                    const entry = p.entry_price ?? 0;
                    const current = p.current_price ?? entry;
                    const pnlPct = entry > 0
                      ? (isBuy ? ((current - entry) / entry) * 100 : ((entry - current) / entry) * 100)
                      : 0;
                    const isWin = pnlPct >= 0;
                    return (
                      <div key={i} className="rounded-lg border border-violet-500/15 bg-background/40 px-3 py-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "rounded px-1.5 py-0.5 text-[9px] font-bold",
                              isBuy ? "bg-emerald-500/15 text-emerald-400" : "bg-rose-500/15 text-rose-400",
                            )}>
                              {isBuy ? "خرید" : "فروش"}
                            </span>
                            <span className="font-mono text-sm font-semibold">{p.symbol}</span>
                          </div>
                          <span className={cn(
                            "font-mono text-xs font-bold",
                            isWin ? "text-emerald-400" : "text-rose-400",
                          )}>
                            {isWin ? "+" : ""}{pnlPct.toFixed(2)}%
                          </span>
                        </div>
                        <div className="mt-1.5 flex items-center justify-between text-[10px] text-muted-foreground">
                          <span>ورود: {Math.round(entry).toLocaleString("fa-IR")}</span>
                          <span>فعلی: {Math.round(current).toLocaleString("fa-IR")}</span>
                        </div>
                        <div className="mt-1.5 flex items-center justify-between">
                          <div className="flex gap-2 text-[10px] text-muted-foreground">
                            <span>TP: {Math.round(p.tp ?? 0).toLocaleString("fa-IR")}</span>
                            <span>SL: {Math.round(p.sl ?? 0).toLocaleString("fa-IR")}</span>
                          </div>
                          <button
                            onClick={() => closePosition.mutate(p.symbol)}
                            disabled={closePosition.isPending}
                            className="rounded border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 text-[10px] text-rose-400 transition hover:bg-rose-500/20 disabled:opacity-50"
                            type="button"
                            title="فروش به قیمت لحظه‌ای بازار"
                          >
                            فروش
                          </button>
                        </div>
                      </div>
                    );
                  })}
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
                        <span className={cn(
                          "font-mono text-xs font-bold",
                          isWin ? "text-emerald-400" : "text-rose-400",
                        )}>
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
