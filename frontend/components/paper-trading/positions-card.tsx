"use client";

import { Activity, Clock, Target, TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { PositionProgress } from "./position-progress";

interface Position {
  symbol: string;
  side: string;
  entry_price: number;
  quantity: number;
  tp: number;
  sl: number;
  entry_time: number;
  reason: string;
  bot_slug: string;
}

interface Props {
  positions: Position[];
}

export function PaperPositionsCard({ positions }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" />
            پوزیشن‌های باز
          </span>
          <Badge variant="outline">{positions.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
            هنوز پوزیشنی باز نشده
          </div>
        ) : (
          <div className="space-y-2">
            {positions.map((p, i) => {
              const ageMin = Math.floor((Date.now() / 1000 - p.entry_time) / 60);
              return (
                <div
                  key={i}
                  className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold">
                        {p.symbol}
                      </span>
                      <Badge
                        variant="outline"
                        className="border-emerald-500/30 text-[10px] text-emerald-400"
                      >
                        {p.side}
                      </Badge>
                    </div>
                    <span className="text-[10px] text-muted-foreground">
                      {ageMin} دقیقه
                    </span>
                  </div>

                  <div className="mt-3">
                    <PositionProgress
                      entry={p.entry_price}
                      current={p.current_price ?? p.entry_price}
                      tp={p.tp}
                      sl={p.sl}
                    />
                  </div>

                  <div className="mt-3 grid grid-cols-3 gap-2 text-[10px]">
                    <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2">
                      <p className="flex items-center gap-1 text-emerald-400">
                        <Target className="h-3 w-3" />
                        TP
                      </p>
                      <p className="mt-1 font-mono text-xs font-bold text-emerald-400">
                        {formatNum(p.tp)}
                      </p>
                      <p className="text-[9px] text-emerald-400/70">
                        +{(((p.tp / p.entry_price) - 1) * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-2">
                      <p className="flex items-center gap-1 text-amber-400">
                        <TrendingUp className="h-3 w-3" />
                        ورود
                      </p>
                      <p className="mt-1 font-mono text-xs font-bold text-amber-400">
                        {formatNum(p.entry_price)}
                      </p>
                      <p className="text-[9px] text-amber-400/70">
                        مقدار {p.quantity.toFixed(4)}
                      </p>
                    </div>
                    <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-2">
                      <p className="flex items-center gap-1 text-red-400">
                        <TrendingDown className="h-3 w-3" />
                        SL
                      </p>
                      <p className="mt-1 font-mono text-xs font-bold text-red-400">
                        {formatNum(p.sl)}
                      </p>
                      <p className="text-[9px] text-red-400/70">
                        {(((p.sl / p.entry_price) - 1) * 100).toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {p.reason && (
                    <p className="mt-2 text-[10px] text-muted-foreground">
                      {p.reason}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(2) + "K";
  return n.toFixed(4);
}
