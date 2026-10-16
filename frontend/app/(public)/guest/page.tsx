"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Sparkles, Play, Square, RotateCcw, TrendingUp, TrendingDown, Wallet, Target, Activity, Clock, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BackgroundFX } from "@/components/landing/background-fx";
import { GuestSignals } from "@/components/guest/guest-signals";
import { GuestScanner } from "@/components/guest/guest-scanner";
import { GuestPersonality } from "@/components/guest/guest-personality";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { UserBadge } from "@/components/layout/user-badge";
import { cn } from "@/lib/utils";
import {
  useGuest,
  useGuestPaperV3Status,
  useStartGuestPaperV3,
  useStopGuestPaperV3,
  useResetGuestPaperV3,
  useCandlesV2,
  usePlaceGuestOrder,
  useCloseGuestPosition,
  useGuestPrice,
  useMe,
} from "@/lib/queries";
import { getUserToken } from "@/lib/auth";
import { CandlestickChart } from "@/components/charts/candlestick-chart";

const SYMBOLS = [
  { key: "BTCTMN",  fa: "بیت‌کوین" },
  { key: "ETHTMN",  fa: "اتریوم" },
  { key: "USDTTMN", fa: "تتر" },
  { key: "SOLTMN",  fa: "سولانا" },
  { key: "XRPTMN",  fa: "ریپل" },
] as const;

/** 21686999673 → "21,686,999,673" (با , انگلیسی — چون input فقط عدد و کاما قبول می‌کنه) */
function formatNum(s: string): string {
  const digits = s.replace(/[^0-9]/g, "");
  if (!digits) return "";
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/** "21,686,999,673" → "21686999673" (فقط رقم) */
function parseNum(s: string): string {
  return s.replace(/[^0-9]/g, "");
}

const fmt = (n: number | undefined | null, dec: number = 0) =>
  n == null ? "—" : Math.round(n).toLocaleString("fa-IR") + (dec > 0 ? "" : "");

export default function GuestPage() {
  const [symbol, setSymbol] = useState<string>("BTCTMN");
  const [timeframe, setTimeframe] = useState<string>("1h");

  // فرم سفارش دستی
  const [orderSide, setOrderSide] = useState<"buy" | "sell">("buy");
  const [orderSymbol, setOrderSymbol] = useState<string>("BTCTMN");
  const [orderAmount, setOrderAmount] = useState<string>("100000");
  const [orderTp, setOrderTp] = useState<string>("2");
  const [orderSl, setOrderSl] = useState<string>("1");
  const [orderLimitPrice, setOrderLimitPrice] = useState<string>("");

  const [isUser, setIsUser] = useState(false);
  useEffect(() => {
    setIsUser(!!getUserToken());
  }, []);

  const me = useMe();
  const guest = useGuest();
  const status = useGuestPaperV3Status();
  const candles = useCandlesV2(symbol, timeframe, 200);
  const startPaper = useStartGuestPaperV3();
  const stopPaper = useStopGuestPaperV3();
  const resetPaper = useResetGuestPaperV3();
  const placeOrder = usePlaceGuestOrder();
  const closePosition = useCloseGuestPosition();
  const marketPrice = useGuestPrice(orderSymbol, true);

  // auto-fill قیمت پیشنهادی با قیمت بازار (وقتی نماد عوض می‌شه)
  useEffect(() => {
    if (marketPrice.data?.price) {
      setOrderLimitPrice(formatNum(String(Math.round(marketPrice.data.price))));
    }
  }, [orderSymbol, marketPrice.data?.price]);

  const data = status.data;
  const isRunning = data?.is_running ?? false;
  const userCapital = (me.data as any)?.capital_total;
  const capital = isUser && userCapital
    ? userCapital
    : (data?.capital ?? guest.data?.capital_total ?? 500_000);
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
              چارت {SYMBOLS.find((s) => s.key === symbol)?.fa ?? symbol}
            </CardTitle>
            <div className="flex items-center gap-2">
              {/* Timeframe */}
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
              {/* Symbol */}
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
              <CandlestickChart
                candles={candles.data.candles}
                height={400}
                showVolume
                interactive
              />
            )}
          </CardContent>
        </Card>
      </section>

      {/* ─── Signals + Scanner + Personality ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <div className="grid gap-4 lg:grid-cols-3">
          <GuestSignals symbol={symbol} timeframe={timeframe} />
          <GuestScanner />
          <GuestPersonality symbol={symbol} timeframe={timeframe} />
        </div>
      </section>

      {/* ─── Disclaimer + Manual Order ─── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_1.5fr]">
          {/* Disclaimer */}
          <Card className="border-amber-500/30 bg-amber-500/5 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-amber-300">
                ⚠️ شبیه‌سازی، نه ترید واقعی
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
              <p>
                سفارش‌هایی که این‌جا ثبت می‌کنی <span className="font-bold text-amber-300">در orderbook والکس نمی‌رن</span>.
                فقط توی state شبیه‌سازی مهمان ذخیره می‌شن.
              </p>
              <p>
                ترید واقعی تفاوت‌های مهمی داره:
              </p>
              <ul className="mr-4 list-disc space-y-1">
                <li>نقدینگی واقعی (سفارش ممکنه fill نشه)</li>
                <li>Slippage (قیمت اجرا با قیمت درخواستی فرق می‌کنه)</li>
                <li>کارمزد صرافی</li>
                <li>تأخیر شبکه</li>
              </ul>
              <p className="pt-2 text-[10px] text-amber-300/70">
                برای ترید واقعی، ثبت‌نام کن و توکن والکس بده.
              </p>
            </CardContent>
          </Card>

          {/* Manual Order Form */}
          <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Zap className="h-5 w-5 text-violet-400" />
                ثبت سفارش دستی (شبیه‌سازی)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Side */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setOrderSide("buy")}
                    className={cn(
                      "rounded-lg border-2 py-2 text-sm font-bold transition",
                      orderSide === "buy"
                        ? "border-emerald-500 bg-emerald-500/20 text-emerald-300"
                        : "border-white/10 text-muted-foreground hover:border-emerald-500/40",
                    )}
                  >
                    خرید
                  </button>
                  <button
                    onClick={() => setOrderSide("sell")}
                    className={cn(
                      "rounded-lg border-2 py-2 text-sm font-bold transition",
                      orderSide === "sell"
                        ? "border-rose-500 bg-rose-500/20 text-rose-300"
                        : "border-white/10 text-muted-foreground hover:border-rose-500/40",
                    )}
                  >
                    فروش
                  </button>
                </div>

                {/* Symbol */}
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">نماد</Label>
                  <div className="flex flex-wrap gap-1">
                    {SYMBOLS.map((s) => (
                      <button
                        key={s.key}
                        onClick={() => setOrderSymbol(s.key)}
                        className={cn(
                          "rounded-full border px-3 py-1 text-[10px] font-medium transition",
                          s.key === orderSymbol
                            ? "border-violet-500 bg-violet-600 text-white"
                            : "border-white/10 text-muted-foreground hover:border-violet-500/40",
                        )}
                      >
                        {s.fa}
                      </button>
                    ))}
                  </div>
                </div>

                {/* مبلغ به تومان */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs text-muted-foreground">مبلغ (تومان)</Label>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      موجودی: {Math.round(capital).toLocaleString("fa-IR")}
                    </span>
                  </div>
                  <Input
                    type="text"
                    inputMode="numeric"
                    value={orderAmount}
                    onChange={(e) => {
                      setOrderAmount(formatNum(e.target.value));
                    }}
                    placeholder="۱۰۰٬۰۰۰"
                    className="h-10 font-mono text-sm"
                  />
                  {/* دکمه‌های درصد سریع */}
                  <div className="flex gap-1">
                    {[25, 50, 75, 100].map((pct) => {
                      const amount = Math.floor(capital * (pct / 100));
                      const active = parseNum(orderAmount) === String(amount);
                      return (
                        <button
                          key={pct}
                          onClick={() => setOrderAmount(formatNum(String(amount)))}
                          type="button"
                          className={cn(
                            "flex-1 rounded-md border px-2 py-1 text-[10px] font-medium transition",
                            active
                              ? "border-violet-500 bg-violet-600/20 text-violet-300"
                              : "border-white/10 text-muted-foreground hover:border-violet-500/40",
                          )}
                        >
                          {pct}٪
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* قیمت پیشنهادی (Limit) */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs text-muted-foreground">
                      قیمت پیشنهادی (اختیاری)
                    </Label>
                    <span className="font-mono text-[10px]">
                      {marketPrice.isLoading ? (
                        <span className="text-muted-foreground">...</span>
                      ) : marketPrice.data?.price ? (
                        <span className="text-violet-300">
                          بازار: {Math.round(marketPrice.data.price).toLocaleString("fa-IR")}
                        </span>
                      ) : (
                        <span className="text-rose-400">قیمت موجود نیست</span>
                      )}
                    </span>
                  </div>
                  <Input
                    type="text"
                    inputMode="numeric"
                    value={orderLimitPrice}
                    onChange={(e) => {
                      setOrderLimitPrice(formatNum(e.target.value));
                    }}
                    placeholder="خالی = به قیمت بازار"
                    className="h-9 font-mono text-xs"
                  />
                  {orderLimitPrice && marketPrice.data?.price && (() => {
                    const lp = parseFloat(parseNum(orderLimitPrice));
                    const mp = marketPrice.data.price!;
                    const isBuy = orderSide === "buy";
                    const ok = isBuy ? lp >= mp : lp <= mp;
                    return (
                      <p className={cn(
                        "text-[10px]",
                        ok ? "text-emerald-400" : "text-amber-400",
                      )}>
                        {ok
                          ? (isBuy ? "✅ قیمت شما ≥ بازار — سفارش پذیرفته می‌شه" : "✅ قیمت شما ≤ بازار — سفارش پذیرفته می‌شه")
                          : (isBuy ? "⚠️ قیمت شما < بازار — سفارش رد می‌شه" : "⚠️ قیمت شما > بازار — سفارش رد می‌شه")}
                      </p>
                    );
                  })()}
                </div>

                {/* TP + SL */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-[10px] text-muted-foreground">TP % (حد سود)</Label>
                    <Input
                      type="text"
                      inputMode="decimal"
                      value={orderTp}
                      onChange={(e) => setOrderTp(e.target.value)}
                      className="h-8 font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[10px] text-muted-foreground">SL % (حد ضرر)</Label>
                    <Input
                      type="text"
                      inputMode="decimal"
                      value={orderSl}
                      onChange={(e) => setOrderSl(e.target.value)}
                      className="h-8 font-mono text-xs"
                    />
                  </div>
                </div>

                {/* Submit */}
                <Button
                  onClick={() =>
                    placeOrder.mutate({
                      side: orderSide,
                      symbol: orderSymbol,
                      amount_tmn: parseFloat(parseNum(orderAmount)) || 0,
                      limit_price: parseFloat(parseNum(orderLimitPrice)) || 0,
                      tp_pct: parseFloat(orderTp) || 2,
                      sl_pct: parseFloat(orderSl) || 1,
                    })
                  }
                  disabled={
                    placeOrder.isPending ||
                    !orderAmount ||
                    parseFloat(parseNum(orderAmount)) <= 0 ||
                    parseFloat(parseNum(orderAmount)) > capital ||
                    openPositions.length >= 10
                  }
                  className={cn(
                    "w-full gap-2",
                    orderSide === "buy"
                      ? "bg-emerald-600 hover:bg-emerald-500"
                      : "bg-rose-600 hover:bg-rose-500",
                  )}
                >
                  <Play className="h-4 w-4" />
                  {placeOrder.isPending ? "در حال ثبت..." : `ثبت ${orderSide === "buy" ? "خرید" : "فروش"}`}
                </Button>

                {openPositions.length >= 10 && (
                  <p className="text-center text-[10px] text-amber-400">
                    سقف ۱۰ پوزیشن باز پر است
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
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
                          >
                            بستن
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
