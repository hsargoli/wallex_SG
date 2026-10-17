"use client";

import Link from "next/link";
import { PieChart, ArrowUpRight, TrendingUp, TrendingDown, Minus, ArrowDown, Wallet } from "lucide-react";
import { useWallexStatus, useBatchSignals, useMarkets } from "@/lib/queries";
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

// کامپوننت اسپارک‌لاین برای نمایش روند قیمت
function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (!data || data.length < 2) return null;
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
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-8 mt-2 opacity-60" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}

export function PortfolioSignals() {
  const wallex = useWallexStatus();
  const markets = useMarkets();

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

  // ترکیب داده‌ها و مرتب‌سازی بر اساس ارزش
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

        return {
          asset: b.asset,
          balance,
          symbol,
          price: price > 0 ? price : null,
          change24: market?.daily_change_percent ? Number(market.daily_change_percent) : (sig?.change_24h ?? null),
          sig,
          value,
        };
      });

    // مرتب‌سازی از بیشترین ارزش به کمترین
    return list.sort((a, b) => b.value - a.value);
  }, [wallex.data, marketMap, signalMap]);

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
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
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
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
                  className="relative overflow-hidden rounded-xl border border-white/10 bg-white/[0.02] p-4 transition-all hover:bg-white/[0.05] hover:border-violet-500/30"
                >
                  {/* هدر کارت: آیکون + نام + سیگنال */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-500/10 text-xs font-bold text-violet-300">
                        {row.asset.slice(0, 3)}
                      </div>
                      <div>
                        <div className="font-bold text-sm">{row.asset}</div>
                        <div className="text-[10px] text-muted-foreground" dir="ltr">
                          {Number(row.balance).toLocaleString("en-US", { maximumFractionDigits: 4 })} units
                        </div>
                      </div>
                    </div>
                    {isBuy && <Badge className="bg-emerald-600/20 text-emerald-300 text-[10px]">خرید {conf ? `${conf}%` : ""}</Badge>}
                    {isSell && <Badge className="bg-rose-600/20 text-rose-300 text-[10px]">فروش {conf ? `${conf}%` : ""}</Badge>}
                    {!isBuy && !isSell && <Badge variant="outline" className="text-[10px] text-muted-foreground">نگهداری</Badge>}
                  </div>

                  {/* اسپارک‌لاین */}
                  {sparkData.length > 0 && <Sparkline data={sparkData} color={sparkColor} />}

                  {/* فوتر کارت: ارزش + قیمت + تغییرات */}
                  <div className="mt-3 flex items-end justify-between border-t border-white/5 pt-3">
                    <div>
                      <div className="text-[10px] text-muted-foreground">ارزش کل</div>
                      <div className="font-mono text-xs font-bold text-foreground" dir="ltr">
                        {formatNumber(row.value, { maximumFractionDigits: 0 })} <span className="text-[10px] text-muted-foreground font-normal">TMN</span>
                      </div>
                    </div>
                    <div className="text-left" dir="ltr">
                      <div className="text-[10px] text-muted-foreground">قیمت</div>
                      <div className="font-mono text-xs">{fmtPrice(row.price)}</div>
                    </div>
                    <div className={cn("text-xs font-bold font-mono", isUp ? "text-emerald-400" : "text-rose-400")}>
                      {fmtPct(row.change24)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
