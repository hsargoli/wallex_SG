"use client";

import { TrendingUp, TrendingDown, Minus, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { usePublicSignals } from "@/lib/queries";
import { cn } from "@/lib/utils";

const SIGNAL_FA: Record<string, string> = {
  buy: "خرید",
  sell: "فروش",
  hold: "نگه‌داری",
};

const STRENGTH_FA: Record<string, string> = {
  weak: "ضعیف",
  medium: "متوسط",
  strong: "قوی",
};

export function GuestSignals({ symbol, timeframe = "1h" }: { symbol: string; timeframe?: string }) {
  const q = usePublicSignals(symbol, timeframe);
  const d = q.data as any;

  const isBuy = d?.signal === "buy";
  const isSell = d?.signal === "sell";
  const isHold = d?.signal === "hold";

  return (
    <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-violet-400" />
            سیگنال {symbol}
          </span>
          {d?.timeframe && (
            <Badge variant="outline" className="border-violet-500/30 text-[10px] text-violet-300">
              {d.timeframe}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : q.isError || !d ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            سیگنالی در دسترس نیست
          </div>
        ) : (
          <div className="space-y-4">
            {/* Badge اصلی */}
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-xl",
                  isBuy
                    ? "bg-emerald-500/20 text-emerald-400"
                    : isSell
                      ? "bg-rose-500/20 text-rose-400"
                      : "bg-muted/50 text-muted-foreground",
                )}
              >
                {isBuy ? (
                  <TrendingUp className="h-6 w-6" />
                ) : isSell ? (
                  <TrendingDown className="h-6 w-6" />
                ) : (
                  <Minus className="h-6 w-6" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-baseline gap-2">
                  <span
                    className={cn(
                      "text-xl font-bold",
                      isBuy ? "text-emerald-400" : isSell ? "text-rose-400" : "text-foreground",
                    )}
                  >
                    {SIGNAL_FA[d.signal] ?? d.signal}
                  </span>
                  {d.strength && (
                    <span className="text-xs text-muted-foreground">
                      · {STRENGTH_FA[d.strength] ?? d.strength}
                    </span>
                  )}
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <div className="h-1.5 flex-1 rounded-full bg-muted/30">
                    <div
                      className={cn(
                        "h-full rounded-full",
                        isBuy
                          ? "bg-emerald-400"
                          : isSell
                            ? "bg-rose-400"
                            : "bg-muted-foreground/40",
                      )}
                      style={{ width: `${d.confidence ?? 0}%` }}
                    />
                  </div>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {d.confidence}%
                  </span>
                </div>
              </div>
            </div>

            {/* دلایل */}
            {d.reasons && d.reasons.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60">
                  دلایل
                </p>
                <ul className="space-y-1">
                  {d.reasons.slice(0, 4).map((r: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-muted-foreground">
                      <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-violet-400" />
                      <span className="leading-relaxed">{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
