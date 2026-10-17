"use client";

import Link from "next/link";
import { PieChart, ArrowUpRight, TrendingUp, TrendingDown, Minus, ArrowDown, Wallet } from "lucide-react";
import { useWallexStatus, useBatchSignals, useMarkets, useWallexPnl } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useMemo } from "react";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

function fmtPrice(p: string | number | null | undefined): string {
  if (p == null) return "—";
  const n = Number(p);
  if (!Number.isFinite(n) || n === 0) return "—";
  if (n < 0.01) return n.toFixed(6);
  if (n < 1) return n.toFixed(4);
  return formatNumber(n, { maximumFractionDigits: 0 });
}

function fmtPct(p: number | null | undefined): string {
  if (p == null) return "—";
  return `${p >= 0 ? "+" : ""}${p.toFixed(2)}%`;
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (!data || data.length < 2) return <div className="h-8 w-full" />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 100;
  const height = 30;
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");
  
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-8 opacity-80" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" />
    </svg>
  );
}

export function PortfolioSignals() {
  const wallex = useWallexStatus();
  const markets = useMarkets();
  const pnlData = useWallexPnl();

  const assets = useMemo(() => {
    if (!wallex.data?.balances) return [];
    return wallex.data.balances
      .filter((b) => Number(b.total) > 0 && b.asset !== "TMN")
      .map((b) => `${b.asset}TMN`);
  }, [wallex.data]);

  const signals = useBatchSignals(assets, "1h");

  const marketMap = useMemo(() => {
    if (!markets.data?.items) return {};
    const map: Record<string, any> = {};
    for (const m of markets.data.items) {
      map[m.symbol] = m;
    }
    return map;
  }, [markets.data]);

  const signalMap = useMemo(() => {
    if (!signals.data?.signals) return {};
    const map: Record<string, any> = {};
    for (const s of signals.data.signals) {
      map[s.symbol] = s;
    }
    return map;
  }, [signals.data]);

  const rows = useMemo(() => {
    if (!wallex.data?.balances) return [];
    
    const list = wallex.data.balances
      .filter((b) => Number(b.total) > 0 && b.asset !== "TMN")
      .map((b) => {
        const symbol = `${b.asset}TMN`;
        const market = marketMap[symbol];
        const sig = signalMap[symbol];
        
        const price = market?.last_price ? Number(market.last_price) : (sig?.current_price ? Number(sig.current_price) : 0);
        const balance = Number(b.total);
        const value = balance * price;

        // ── merge با cost_basis (backend) + market price (frontend) ──
        const cb = pnlData.data?.assets?.find((a) => a.symbol === symbol);

        // محاسبه‌ی PnL سمت کلاینت
        const totalCost = cb ? Number(cb.total_cost) : null;
        const currentValue = (price > 0 && balance > 0) ? price * balance : null;
        const hasUnknown = cb?.has_unknown_history ?? false;
        const unrealizedPnl = (
          totalCost !== null
          && totalCost > 0
          && currentValue !== null
          && !hasUnknown
        ) ? currentValue - totalCost : null;
        const unrealizedPnlPct = (
          unrealizedPnl !== null && totalCost !== null && totalCost > 0
        ) ? (unrealizedPnl / totalCost) * 100 : null;

        return {
          asset: b.asset,
          balance,
          symbol,
          price: price > 0 ? price : null,
          change24: market?.daily_change_percent ? Number(market.daily_change_percent) : (sig?.change_24h ?? null),
          sig,
          value,
          // pnl به شکل سازگار با UI فعلی (avg_cost از backend، بقیه محاسبه‌شده)
          pnl: {
            avg_cost: cb?.avg_cost ?? null,
            total_cost: totalCost,
            has_unknown_history: hasUnknown,
            unrealized_pnl: unrealizedPnl,
            unrealized_pnl_pct: unrealizedPnlPct,
          },
        };
      });

    return list.sort((a, b) => b.value - a.value);
  }, [wallex.data, marketMap, signalMap, pnlData.data]);

  const isLoading = wallex.isLoading || markets.isLoading;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-violet-400" />
            دارایی‌های من (والکس)
            <span className="text-[10px] font-normal text-muted-foreground flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded-full">
              <ArrowDown className="h-3 w-3" /> بر اساس ارزش
            </span>
          </span>
          <Link href="/signals">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              مشاهده همه
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        )}

        {!isLoading && rows.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <PieChart className="mb-2 h-8 w-8 opacity-20" />
            <p className="text-sm">هنوز دارایی غیرصفر نداری</p>
            <Button asChild variant="outline" size="sm" className="mt-4">
              <Link href="/settings/wallex">اتصال به والکس</Link>
            </Button>
          </div>
        )}

        {!isLoading && rows.length > 0 && (
          <div className="flex flex-col gap-2">
            {rows.map((row) => {
              const sig = row.sig;
              const action = sig?.signal ?? "hold";
              const isBuy = action === "buy";
              const isSell = action === "sell";
              const conf = sig?.confidence;
              const sparkData = sig?.sparkline || [];
              const isUp = (row.change24 ?? 0) >= 0;
              const sparkColor = isUp ? "#34d399" : "#fb7185";

              return (
                <div
                  key={row.symbol}
                  className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-all hover:bg-white/[0.04] hover:border-violet-500/20"
                >
                  {/* ستون ۱: دارایی و موجودی */}
                  <div className="flex items-center gap-3 w-full sm:w-[180px] shrink-0">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-violet-500/10 text-xs font-bold text-violet-300">
                      {row.asset.slice(0, 3)}
                    </div>
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm">{row.asset}</span>
                        {isBuy && <Badge className="bg-emerald-600/20 text-emerald-300 text-[10px] h-5 px-1.5">خرید {conf ? `${conf}%` : ""}</Badge>}
                        {isSell && <Badge className="bg-rose-600/20 text-rose-300 text-[10px] h-5 px-1.5">فروش {conf ? `${conf}%` : ""}</Badge>}
                        {!isBuy && !isSell && <Badge variant="outline" className="text-[10px] text-muted-foreground h-5 px-1.5">نگهداری</Badge>}
                      </div>
                      <span className="text-[10px] text-muted-foreground" dir="ltr">
                        {Number(row.balance).toLocaleString("en-US", { maximumFractionDigits: 4 })} units
                      </span>
                    </div>
                  </div>

                  {/* ستون ۲: نمودار Sparkline (فقط دسکتاپ) */}
                  <div className="hidden md:block w-[120px] shrink-0 px-2">
                    <Sparkline data={sparkData} color={sparkColor} />
                  </div>

                  {/* ستون ۳: دیتای عددی */}
                  <div className="grid grid-cols-2 sm:flex sm:items-center gap-4 flex-1 justify-end w-full">
                    {/* ارزش بازار */}
                    <div className="text-right sm:w-28">
                      <div className="text-[10px] text-muted-foreground" title="موجودی × قیمت لحظه‌ای بازار">
                        ارزش بازار
                      </div>
                      <div className="font-mono text-xs font-bold text-foreground" dir="ltr">
                        {formatNumber(row.value, { maximumFractionDigits: 0 })} <span className="text-[10px] text-muted-foreground font-normal">TMN</span>
                      </div>
                    </div>

                    {/* میانگین خرید */}
                    <div className="text-right sm:w-24">
                      <div className="text-[10px] text-muted-foreground" title="هزینه‌ی کل خرید تقسیم بر تعداد واحد (روش FIFO)">
                        میانگین خرید
                      </div>
                      <div className="font-mono text-xs" dir="ltr">
                        {row.pnl?.avg_cost ? fmtPrice(row.pnl.avg_cost) : "—"}
                      </div>
                    </div>

                    {/* قیمت فعلی */}
                    <div className="text-right sm:w-24">
                      <div className="text-[10px] text-muted-foreground" title="آخرین قیمت معامله‌شده در بازار">
                        قیمت فعلی
                      </div>
                      <div className="font-mono text-xs" dir="ltr">{fmtPrice(row.price)}</div>
                    </div>

                    {/* تغییر ۲۴h */}
                    <div className="text-left sm:w-20">
                      <div className="text-[10px] text-muted-foreground" title="درصد تغییر قیمت بازار در ۲۴ ساعت گذشته">
                        تغییر ۲۴h
                      </div>
                      <div className={cn("font-mono text-xs font-bold", isUp ? "text-emerald-400" : "text-rose-400")} dir="ltr">
                        {fmtPct(row.change24)}
                      </div>
                    </div>

                    {/* سود/زیان */}
                    <div className="text-left sm:w-24">
                      <div className="text-[10px] text-muted-foreground" title="ارزش بازار − هزینه‌ی خرید (درصد نسبت به هزینه)">
                        سود/زیان
                      </div>
                      {row.pnl?.unrealized_pnl ? (
                        <div
                          className={cn(
                            "font-mono text-xs font-bold",
                            Number(row.pnl.unrealized_pnl) > 0
                              ? "text-emerald-400"
                              : Number(row.pnl.unrealized_pnl) < 0
                                ? "text-rose-400"
                                : "text-muted-foreground"
                          )}
                          dir="ltr"
                        >
                          {Number(row.pnl.unrealized_pnl) > 0 ? "+" : ""}
                          {formatNumber(Number(row.pnl.unrealized_pnl), { maximumFractionDigits: 0 })}
                          {row.pnl.unrealized_pnl_pct && (
                            <span className="mr-1 text-[10px] font-normal opacity-70">
                              ({Number(row.pnl.unrealized_pnl_pct) > 0 ? "+" : ""}
                              {Number(row.pnl.unrealized_pnl_pct).toFixed(1)}%)
                            </span>
                          )}
                        </div>
                      ) : row.pnl?.has_unknown_history ? (
                        <div className="text-[10px] text-amber-400" title="خرید قبل از تاریخچه — PnL نامشخص">
                          نامشخص
                        </div>
                      ) : (
                        <div className="text-xs text-muted-foreground">—</div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* راهنمای ستون‌ها */}
        {!isLoading && rows.length > 0 && (
          <div className="mt-4 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-[10px] text-muted-foreground">
            <div className="mb-2 font-bold text-[11px] text-foreground">📖 راهنمای ستون‌ها</div>
            <div className="grid gap-1.5 sm:grid-cols-2">
              <div>
                <span className="font-semibold text-foreground">ارزش بازار:</span>{" "}
                موجودی × قیمت لحظه‌ای بازار (پولی که اگه الان بفروشی به دستت میاد)
              </div>
              <div>
                <span className="font-semibold text-foreground">میانگین خرید:</span>{" "}
                هزینه‌ی کل خرید ÷ تعداد واحد (به روش FIFO — اولین خرید اول مصرف می‌شه)
              </div>
              <div>
                <span className="font-semibold text-foreground">قیمت فعلی:</span>{" "}
                آخرین قیمت معامله‌شده در بازار
              </div>
              <div>
                <span className="font-semibold text-foreground">تغییر ۲۴h:</span>{" "}
                درصد تغییر قیمت بازار در ۲۴ ساعت گذشته (ربطی به سود تو نداره)
              </div>
              <div className="sm:col-span-2">
                <span className="font-semibold text-emerald-400">سود/زیان:</span>{" "}
                ارزش بازار − هزینه‌ی خرید (درصد نسبت به هزینه). مثبت = سود، منفی = ضرر.
                اگه «نامشخص» باشه، یعنی خریدهایی قبل از تاریخچه‌ی ثبت‌شده در والکس انجام شده.
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
