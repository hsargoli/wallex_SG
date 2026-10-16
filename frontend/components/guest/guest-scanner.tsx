"use client";

import { Radar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { usePublicScanner } from "@/lib/queries";

const fmtVol = (v: string | number) => {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (!Number.isFinite(n)) return "—";
  if (n > 1_000_000_000_000) return `${(n / 1_000_000_000_000).toFixed(1)}T`;
  if (n > 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n > 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n > 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(0);
};

export function GuestScanner() {
  const q = usePublicScanner(1, 5);
  const d = q.data as any;

  return (
    <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Radar className="h-5 w-5 text-violet-400" />
            اسکنر بازار
          </span>
          {d?.total && (
            <Badge variant="outline" className="border-violet-500/30 text-[10px] text-violet-300">
              {d.total.toLocaleString("fa-IR")} نماد
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : q.isError || !d?.items_meta ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            اسکنر در دسترس نیست
          </div>
        ) : (
          <div className="space-y-1.5">
            <div className="grid grid-cols-[1fr_auto] gap-2 px-2 pb-1 text-[9px] uppercase tracking-wider text-muted-foreground/60">
              <span>نماد</span>
              <span>حجم ۲۴h</span>
            </div>
            {d.items_meta.slice(0, 5).map((m: any, i: number) => (
              <div
                key={m.symbol}
                className="grid grid-cols-[1fr_auto] items-center gap-2 rounded-lg border border-violet-500/10 bg-background/40 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="w-4 text-center font-mono text-[10px] text-muted-foreground/50">
                    {i + 1}
                  </span>
                  <span className="font-mono text-xs font-semibold">{m.symbol}</span>
                </div>
                <span className="font-mono text-[10px] text-violet-300">
                  {fmtVol(m.daily_volume)}
                </span>
              </div>
            ))}
            <p className="pt-1 text-center text-[10px] text-muted-foreground/60">
              مرتب‌شده بر اساس حجم ۲۴ ساعته
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
