"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Wallet,
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  Zap,
  Play,
  Square,
  RotateCcw,
  ShieldAlert,
} from "lucide-react";
import {
  useUserPaperV3Status,
  useStartUserPaperV3,
  useStopUserPaperV3,
  useResetUserPaperV3,
  usePlaceUserOrder,
  useCloseUserPosition,
  usePublicPrice,
} from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const SYMBOLS = [
  { key: "BTCTMN", fa: "بیت‌کوین" },
  { key: "ETHTMN", fa: "اتریوم" },
  { key: "USDTTMN", fa: "تتر" },
  { key: "SOLTMN", fa: "سولانا" },
  { key: "XRPTMN", fa: "ریپل" },
] as const;

const fmt = (n: number | undefined | null) =>
  n == null ? "—" : Math.round(n).toLocaleString("fa-IR");

const fmtNum = (n: number | undefined | null, digits = 2) =>
  n == null ? "—" : n.toLocaleString("fa-IR", { maximumFractionDigits: digits });

function formatNum(s: string): string {
  const digits = s.replace(/[^0-9]/g, "");
  if (!digits) return "";
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function parseNum(s: string): string {
  return s.replace(/[^0-9]/g, "");
}

export default function ManualPaperPage() {
  const status = useUserPaperV3Status();
  const startPaper = useStartUserPaperV3();
  const stopPaper = useStopUserPaperV3();
  const resetPaper = useResetUserPaperV3();
  const placeOrder = usePlaceUserOrder();
  const closePosition = useCloseUserPosition();

  const [orderSymbol, setOrderSymbol] = useState("BTCTMN");
  const [orderAmount, setOrderAmount] = useState("100000");
  const [orderTp, setOrderTp] = useState("2");
  const [orderSl, setOrderSl] = useState("1");
  const [orderLimitPrice, setOrderLimitPrice] = useState("");

  const marketPrice = usePublicPrice(orderSymbol, true);

  const data = status.data as
    | {
        is_running?: boolean;
        capital_total?: number;
        capital?: number;
        capital_available?: number;
        equity?: number;
        total_pnl?: number;
        total_pnl_pct?: number;
        total_trades?: number;
        wins?: number;
        losses?: number;
        open_positions?: Array<{
          symbol: string;
          side: string;
          entry_price: number;
          current_price?: number;
          cost?: number;
        }>;
        trades?: Array<{
          symbol: string;
          side: string;
          entry_price: number;
          exit_price?: number;
          pnl?: number;
          pnl_pct?: number;
        }>;
      }
    | undefined;

  const isRunning = data?.is_running ?? false;
  const capital = data?.capital_available ?? data?.capital ?? 10_000_000;
  const equity = data?.equity ?? capital;
  const totalPnl = data?.total_pnl ?? 0;
  const totalPnlPct = data?.total_pnl_pct ?? 0;
  const trades = data?.total_trades ?? 0;
  const wins = data?.wins ?? 0;
  const losses = data?.losses ?? 0;
  const openPositions = data?.open_positions ?? [];
  const closedTrades = data?.trades ?? [];

  const handleStart = () => {
    startPaper.mutate({
      initial_capital: 10_000_000,
      position_size_pct: 30,
    });
  };

  const handlePlaceOrder = () => {
    const amount = Number(parseNum(orderAmount));
    if (!amount) return;
    placeOrder.mutate({
      side: "buy",
      symbol: orderSymbol,
      amount_tmn: amount,
      tp_pct: Number(orderTp) || undefined,
      sl_pct: Number(orderSl) || undefined,
      limit_price: Number(parseNum(orderLimitPrice)) || undefined,
    });
  };

  if (status.isLoading) {
    return (
      <div className="container py-8 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <Link
              href="/paper-trading"
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              <ArrowRight className="h-3 w-3" />
              Paper Trading (ربات‌ها)
            </Link>
          </div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Zap className="h-6 w-6 text-violet-400" />
            سفارش دستی (شبیه‌سازی)
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            سفارش‌های خودت را روی Paper ثبت کن — بدون ریسک، با سرمایه‌ی مجازی.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <Button
              onClick={handleStart}
              disabled={startPaper.isPending}
              className="gap-2 bg-violet-600 hover:bg-violet-700"
            >
              <Play className="h-4 w-4" />
              {startPaper.isPending ? "در حال شروع..." : "شروع Paper"}
            </Button>
          ) : (
            <>
              <Button
                onClick={() => stopPaper.mutate()}
                disabled={stopPaper.isPending}
                variant="destructive"
                className="gap-2"
              >
                <Square className="h-4 w-4" />
                توقف
              </Button>
              <Button
                onClick={() => resetPaper.mutate()}
                disabled={resetPaper.isPending || isRunning}
                variant="outline"
                size="icon"
                title="ریست"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Status Banner */}
      <Card
        className={cn(
          "border-2",
          isRunning
            ? "border-violet-500/40 bg-violet-500/5"
            : "border-white/10",
        )}
      >
        <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "h-3 w-3 rounded-full",
                isRunning
                  ? "animate-pulse bg-emerald-400"
                  : "bg-muted-foreground/40",
              )}
            />
            <div>
              <p className="font-semibold">
                {isRunning ? "در حال اجرا" : "متوقف"}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRunning
                  ? "سفارش‌های جدید در Paper ثبت می‌شوند"
                  : "برای ثبت سفارش، ابتدا Paper را شروع کن"}
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

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="space-y-1 pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Wallet className="h-3.5 w-3.5" /> سرمایه
            </div>
            <p className="text-2xl font-bold">{fmt(capital)}</p>
            <p className="text-[10px] text-muted-foreground">تومان</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-1 pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Activity className="h-3.5 w-3.5" /> ارزش کل (Equity)
            </div>
            <p className="text-2xl font-bold">{fmt(equity)}</p>
            <p className="text-[10px] text-muted-foreground">تومان</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-1 pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {totalPnl >= 0 ? (
                <TrendingUp className="h-3.5 w-3.5" />
              ) : (
                <TrendingDown className="h-3.5 w-3.5" />
              )}
              سود/زیان
            </div>
            <p
              className={cn(
                "text-2xl font-bold",
                totalPnl >= 0 ? "text-emerald-400" : "text-rose-400",
              )}
            >
              {totalPnl >= 0 ? "+" : ""}
              {fmtNum(totalPnlPct)}٪
            </p>
            <p className="text-[10px] text-muted-foreground">
              {totalPnl >= 0 ? "+" : ""}
              {fmt(totalPnl)} تومان
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-1 pt-5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Target className="h-3.5 w-3.5" /> Win Rate
            </div>
            <p className="text-2xl font-bold">
              {trades > 0 ? Math.round((wins / trades) * 100) : 0}٪
            </p>
            <p className="text-[10px] text-muted-foreground">
              {wins}W / {losses}L
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Form + Disclaimer */}
      <div className="grid gap-4 lg:grid-cols-[1fr_1.5fr]">
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base text-amber-300">
              <ShieldAlert className="h-4 w-4" />
              شبیه‌سازی، نه ترید واقعی
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
            <p>
              سفارش‌ها در{" "}
              <span className="font-bold text-amber-300">
                orderbook والکس نمی‌رن
              </span>
              . فقط در Paper state ذخیره می‌شوند.
            </p>
            <p>ترید واقعی تفاوت‌های مهمی دارد:</p>
            <ul className="mr-4 list-disc space-y-1">
              <li>نقدینگی واقعی (سفارش ممکنه fill نشه)</li>
              <li>Slippage (قیمت اجرا با قیمت درخواستی فرق می‌کنه)</li>
              <li>کارمزد صرافی</li>
              <li>تأخیر شبکه</li>
            </ul>
            <p className="pt-2 text-[10px] text-amber-300/70">
              برای ترید واقعی، به /order-bot برو (نیاز به توکن والکس).
            </p>
          </CardContent>
        </Card>

        <Card className="border-violet-500/15 bg-background/60">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-5 w-5 text-violet-400" />
              ثبت سفارش دستی
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!isRunning && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
                ابتدا دکمه‌ی «شروع Paper» را بزن.
              </div>
            )}

            {/* Side */}
            <div className="grid grid-cols-2 gap-2">
              <div className="col-span-2 rounded-lg border-2 border-emerald-500 bg-emerald-500/20 py-2 text-center text-sm font-bold text-emerald-300">
                خرید دارایی
              </div>
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

            {/* Amount */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-xs text-muted-foreground">
                  مبلغ (تومان)
                </Label>
                <span className="font-mono text-[10px] text-muted-foreground">
                  موجودی: {fmt(capital)}
                </span>
              </div>
              <Input
                type="text"
                inputMode="numeric"
                value={orderAmount}
                onChange={(e) => setOrderAmount(formatNum(e.target.value))}
                placeholder="۱۰۰٬۰۰۰"
                className="h-10 font-mono text-sm"
                disabled={!isRunning}
              />
              <div className="flex gap-1">
                {[25, 50, 75, 100].map((pct) => {
                  const amount = Math.floor(capital * (pct / 100));
                  const active = parseNum(orderAmount) === String(amount);
                  return (
                    <button
                      key={pct}
                      onClick={() => setOrderAmount(formatNum(String(amount)))}
                      type="button"
                      disabled={!isRunning}
                      className={cn(
                        "flex-1 rounded-md border px-2 py-1 text-[10px] font-medium transition",
                        active
                          ? "border-violet-500 bg-violet-600/20 text-violet-300"
                          : "border-white/10 text-muted-foreground hover:border-violet-500/40",
                        !isRunning && "opacity-50 cursor-not-allowed",
                      )}
                    >
                      {pct}٪
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Limit */}
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
                      بازار: {fmt(marketPrice.data.price)}
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
                onChange={(e) => setOrderLimitPrice(formatNum(e.target.value))}
                placeholder="خالی = قیمت بازار"
                className="h-9 font-mono text-xs"
                disabled={!isRunning}
              />
            </div>

            {/* TP/SL */}
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  TP (٪ سود)
                </Label>
                <Input
                  value={orderTp}
                  onChange={(e) => setOrderTp(e.target.value)}
                  className="h-9 font-mono text-xs"
                  disabled={!isRunning}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  SL (٪ ضرر)
                </Label>
                <Input
                  value={orderSl}
                  onChange={(e) => setOrderSl(e.target.value)}
                  className="h-9 font-mono text-xs"
                  disabled={!isRunning}
                />
              </div>
            </div>

            <Button
              onClick={handlePlaceOrder}
              disabled={
                !isRunning || placeOrder.isPending || !parseNum(orderAmount)
              }
              className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              {placeOrder.isPending ? "در حال ثبت..." : "ثبت سفارش"}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Open Positions */}
      {openPositions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              پوزیشن‌های باز ({openPositions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {openPositions.map((p, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{p.symbol}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {p.side === "buy" ? "خرید" : "فروش"}
                    </span>
                    <span className="font-mono text-xs">
                      ورود: {fmt(p.entry_price)}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => closePosition.mutate(p.symbol)}
                    disabled={closePosition.isPending}
                  >
                    بستن
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Trades */}
      {closedTrades.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              آخرین تریدها ({closedTrades.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-xs text-muted-foreground">
                    <th className="text-right py-2 px-2">نماد</th>
                    <th className="text-right py-2 px-2">جهت</th>
                    <th className="text-right py-2 px-2">ورود</th>
                    <th className="text-right py-2 px-2">خروج</th>
                    <th className="text-right py-2 px-2">PnL٪</th>
                  </tr>
                </thead>
                <tbody>
                  {closedTrades
                    .slice(-10)
                    .reverse()
                    .map((t, i) => (
                      <tr key={i} className="border-b border-border/40">
                        <td className="py-2 px-2 font-mono text-xs">
                          {t.symbol}
                        </td>
                        <td className="py-2 px-2 text-xs">
                          {t.side === "buy" ? "خرید" : "فروش"}
                        </td>
                        <td className="py-2 px-2 font-mono text-xs">
                          {fmt(t.entry_price)}
                        </td>
                        <td className="py-2 px-2 font-mono text-xs">
                          {t.exit_price ? fmt(t.exit_price) : "—"}
                        </td>
                        <td
                          className={cn(
                            "py-2 px-2 font-mono text-xs",
                            (t.pnl_pct ?? 0) >= 0
                              ? "text-emerald-400"
                              : "text-rose-400",
                          )}
                        >
                          {t.pnl_pct != null
                            ? `${t.pnl_pct >= 0 ? "+" : ""}${fmtNum(t.pnl_pct)}٪`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {isRunning &&
        closedTrades.length === 0 &&
        openPositions.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-sm text-muted-foreground">
              هنوز تریدی ثبت نشده — اولین سفارش را ثبت کن.
            </CardContent>
          </Card>
        )}
    </div>
  );
}
