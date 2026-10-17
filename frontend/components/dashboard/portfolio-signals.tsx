"use client";

import Link from "next/link";
import { PieChart, ArrowUpRight, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useWallexStatus, useBatchSignals } from "@/lib/queries";
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
  if (!Number.isFinite(n)) return "—";
  return formatNumber(n, { maximumFractionDigits: 0 });
}

function fmtPct(p: number | null | undefined): string {
  if (p == null) return "—";
  return `${p >= 0 ? "+" : ""}${p.toFixed(2)}%`;
}

export function PortfolioSignals() {
  const wallex = useWallexStatus();

  const assets = useMemo(() => {
    if (!wallex.data?.balances) return [];
    return wallex.data.balances
      .filter((b) => Number(b.total) > 0 && b.asset !== "TMN")
      .map((b) => `${b.asset}TMN`);
  }, [wallex.data]);

  const signals = useBatchSignals(assets, "1h");

  const signalMap = useMemo(() => {
    if (!signals.data?.signals) return {};
    const map: Record<string, any> = {};
    for (const s of signals.data.signals) {
      map[s.symbol] = s;
    }
    return map;
  }, [signals.data]);

  const isLoading = wallex.isLoading || (assets.length > 0 && signals.isLoading);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <PieChart className="h-4 w-4 text-violet-400" />
            دارایی‌های من (والکس)
            {signals.isFetching && assets.length > 0 && (
              <span className="text-[10px] font-normal text-muted-foreground">
                (در حال بروزرسانی...)
              </span>
            )}
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
        {/* Loading */}
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}

        {/* Empty */}
        {!isLoading && assets.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <PieChart className="mb-2 h-8 w-8 opacity-20" />
            <p className="text-sm">هنوز دارایی غیرصفر نداری</p>
            <Button asChild variant="outline" size="sm" className="mt-4">
              <Link href="/settings/wallex">اتصال به والکس</Link>
            </Button>
          </div>
        )}

        {/* Table */}
        {!isLoading && assets.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[10px] text-muted-foreground">
                <tr className="border-b border-white/10">
                  <th className="px-2 py-2 text-right font-medium">دارایی</th>
                  <th className="px-2 py-2 text-left font-medium">موجودی</th>
                  <th className="px-2 py-2 text-left font-medium">قیمت فعلی</th>
                  <th className="px-2 py-2 text-left font-medium">تغییر ۲۴h</th>
                  <th className="px-2 py-2 text-center font-medium">سیگنال</th>
                  <th className="px-2 py-2 text-left font-medium" title="حد سود / حد ضرر">TP / SL</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((symbol) => {
                  const bal = wallex.data?.balances?.find(
                    (b) => `${b.asset}TMN` === symbol
                  );
                  const sig = signalMap[symbol];
                  const action = sig?.signal ?? "hold";
                  const isBuy = action === "buy";
                  const isSell = action === "sell";
                  const change24 = sig?.change_24h ?? null;
                  const conf = sig?.confidence;
                  const currentPrice = sig?.current_price;
                  const tp = sig?.take_profit;
                  const sl = sig?.stop_loss;

                  return (
                    <tr
                      key={symbol}
                      className="border-b border-white/5 transition hover:bg-white/5"
                    >
                      <td className="px-2 py-2">
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {bal?.asset ?? symbol}
                        </Badge>
                      </td>
                      <td className="px-2 py-2 text-left font-mono text-xs" dir="ltr">
                        {bal
                          ? Number(bal.total).toLocaleString("en-US", {
                              maximumFractionDigits: 6,
                            })
                          : "—"}
                      </td>
                      <td className="px-2 py-2 text-left font-mono text-xs" dir="ltr">
                        {fmtPrice(currentPrice)}
                      </td>
                      <td
                        className={cn(
                          "px-2 py-2 text-left font-mono text-xs",
                          change24 == null
                            ? "text-muted-foreground"
                            : change24 > 0
                              ? "text-emerald-400"
                              : change24 < 0
                                ? "text-rose-400"
                                : "text-muted-foreground"
                        )}
                        dir="ltr"
                      >
                        {fmtPct(change24)}
                      </td>
                      <td className="px-2 py-2 text-center">
                        <div className="inline-flex items-center gap-1">
                          {isBuy && (
                            <Badge className="bg-emerald-600/20 text-emerald-300 text-[10px]">
                              <TrendingUp className="mr-1 h-3 w-3" />
                              خرید {conf ? `${conf}%` : ""}
                            </Badge>
                          )}
                          {isSell && (
                            <Badge className="bg-rose-600/20 text-rose-300 text-[10px]">
                              <TrendingDown className="mr-1 h-3 w-3" />
                              فروش {conf ? `${conf}%` : ""}
                            </Badge>
                          )}
                          {!isBuy && !isSell && (
                            <Badge variant="outline" className="text-[10px] text-muted-foreground">
                              <Minus className="mr-1 h-3 w-3" />
                              نگهداری
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-2 py-2 text-left font-mono text-[10px] text-muted-foreground" dir="ltr">
                        {tp && sl ? `${fmtPrice(tp)} / ${fmtPrice(sl)}` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-3 text-[10px] text-muted-foreground">
              💡 قیمت خرید (cost basis) از API View دریافت نمی‌شه. برای مشاهده‌ی
              آن، به توکن Trade نیاز است (فاز بعدی).
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
