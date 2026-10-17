"use client";

import Link from "next/link";
import { ClipboardList, ArrowUpRight, Clock } from "lucide-react";
import { useUserPaperV3Status } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export function OrdersTimeline() {
  const paper = useUserPaperV3Status();
  const data = paper.data as Record<string, any> | undefined;
  
  const recentTrades = data?.recent_trades ?? [];
  const openPositions = data?.open_positions ?? [];

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <ClipboardList className="h-4 w-4 text-blue-400" />
            پوزیشن‌ها و سفارش‌های Paper
          </span>
          <Link href="/guest">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              مشاهده همه
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        {paper.isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}

        {!paper.isLoading && openPositions.length === 0 && recentTrades.length === 0 && (
          <div className="flex h-full min-h-[200px] flex-col items-center justify-center text-center text-muted-foreground">
            <ClipboardList className="mb-2 h-8 w-8 opacity-20" />
            <p className="text-sm">هنوز سفارشی ثبت نشده</p>
            <Button asChild variant="outline" size="sm" className="mt-4">
              <Link href="/guest">ثبت اولین سفارش</Link>
            </Button>
          </div>
        )}

        <div className="space-y-4">
          {openPositions.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold text-muted-foreground">پوزیشن‌های باز ({openPositions.length})</h4>
              <div className="space-y-2">
                {openPositions.map((p: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-white/5 bg-white/5 p-2 text-sm">
                    <div className="flex flex-col">
                      <span className="font-bold">{p.symbol}</span>
                      <span className="text-[10px] text-muted-foreground">{p.side === 'buy' ? 'خرید' : 'فروش'} @ {formatNumber(p.entry_price)}</span>
                    </div>
                    <div className="text-left font-mono text-xs">
                      {formatNumber(p.current_price)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {recentTrades.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold text-muted-foreground">بسته‌شده‌ها ({recentTrades.length})</h4>
              <div className="space-y-2">
                {recentTrades.slice(0, 3).map((t: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-white/5 p-2 text-sm">
                    <div className="flex flex-col">
                      <span className="font-bold">{t.symbol}</span>
                      <span className="text-[10px] text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" /> {t.exit_reason}</span>
                    </div>
                    <div className={cn("text-left font-mono text-xs", t.pnl > 0 ? "text-emerald-400" : "text-rose-400")}>
                      {t.pnl > 0 ? "+" : ""}{formatNumber(t.pnl)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
