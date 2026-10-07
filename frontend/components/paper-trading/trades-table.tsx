"use client";

import { Clock, History } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Trade {
  symbol: string;
  side: string;
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct: number;
  exit_reason: string;
  duration_minutes: number;
  bot_slug: string;
}

interface Props {
  trades: Trade[];
}

export function PaperTradesTable({ trades }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <History className="h-5 w-5 text-blue-400" />
            تاریخچه تریدها
          </span>
          <Badge variant="outline">{trades.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {trades.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
            هنوز تریدی ثبت نشده
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-right text-[11px] text-muted-foreground">
                  <th className="pb-2 font-medium">#</th>
                  <th className="pb-2 font-medium">نماد</th>
                  <th className="pb-2 font-medium">ورود</th>
                  <th className="pb-2 font-medium">خروج</th>
                  <th className="pb-2 font-medium">مقدار</th>
                  <th className="pb-2 font-medium">سود</th>
                  <th className="pb-2 font-medium">درصد</th>
                  <th className="pb-2 font-medium">دلیل</th>
                  <th className="pb-2 font-medium">مدت</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t, i) => {
                  const isWin = t.pnl > 0;
                  return (
                    <tr
                      key={i}
                      className="border-b border-white/5 transition hover:bg-white/[0.02]"
                    >
                      <td className="py-2 font-mono text-[11px] text-muted-foreground">
                        {i + 1}
                      </td>
                      <td className="py-2 font-mono text-xs font-semibold">
                        {t.symbol}
                      </td>
                      <td className="py-2 font-mono text-[11px]">
                        {formatNum(t.entry_price)}
                      </td>
                      <td className="py-2 font-mono text-[11px]">
                        {formatNum(t.exit_price)}
                      </td>
                      <td className="py-2 font-mono text-[11px] text-muted-foreground">
                        {t.quantity.toFixed(4)}
                      </td>
                      <td
                        className={cn(
                          "py-2 font-mono text-[11px] font-bold",
                          isWin ? "text-emerald-400" : "text-red-400",
                        )}
                      >
                        {isWin ? "+" : ""}
                        {formatNum(t.pnl)}
                      </td>
                      <td className="py-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            "font-mono text-[10px]",
                            isWin
                              ? "border-emerald-500/30 text-emerald-400"
                              : "border-red-500/30 text-red-400",
                          )}
                        >
                          {isWin ? "+" : ""}
                          {t.pnl_pct.toFixed(2)}%
                        </Badge>
                      </td>
                      <td className="py-2">
                        <span className="text-[10px] text-muted-foreground">
                          {t.exit_reason}
                        </span>
                      </td>
                      <td className="py-2 font-mono text-[10px] text-muted-foreground">
                        {t.duration_minutes}m
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(2) + "K";
  if (n >= 1) return n.toFixed(2);
  return n.toFixed(4);
}
