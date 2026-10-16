"use client";

import { Brain } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { usePublicAnalysis } from "@/lib/queries";

const REGIME_FA: Record<string, string> = {
  trending_up: "صعودی",
  trending_down: "نزولی",
  ranging: "رنج",
  choppy: "پرنوسان",
};

const REGIME_COLOR: Record<string, string> = {
  trending_up: "#10b981",
  trending_down: "#f43f5e",
  ranging: "#a78bfa",
  choppy: "#f59e0b",
};

export function GuestPersonality({ symbol, timeframe = "1h" }: { symbol: string; timeframe?: string }) {
  const q = usePublicAnalysis(symbol, timeframe);
  const d = q.data as any;

  // donut data
  const donut = d?.regime_counts
    ? Object.entries(d.regime_counts).map(([k, v]: [string, any]) => ({
        key: k,
        label: REGIME_FA[k] ?? k,
        value: v as number,
        color: REGIME_COLOR[k] ?? "#a78bfa",
      }))
    : [];

  const total = donut.reduce((s, x) => s + x.value, 0);
  let offset = 0;
  const R = 28;
  const C = 2 * Math.PI * R;

  return (
    <Card className="border-violet-500/15 bg-background/60 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-violet-400" />
            شخصیت {symbol}
          </span>
          {d?.dominant_regime && (
            <Badge
              variant="outline"
              className="border-violet-500/30 text-[10px]"
              style={{ color: REGIME_COLOR[d.dominant_regime] }}
            >
              غالب: {REGIME_FA[d.dominant_regime] ?? d.dominant_regime}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : q.isError || !d ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            تحلیل در دسترس نیست
          </div>
        ) : (
          <div className="space-y-4">
            {/* Donut */}
            <div className="flex items-center gap-4">
              <svg viewBox="0 0 80 80" className="h-20 w-20 shrink-0">
                <circle cx="40" cy="40" r={R} fill="none" stroke="rgba(139,92,246,0.1)" strokeWidth="10" />
                {donut.map((seg) => {
                  const dash = total > 0 ? (seg.value / total) * C : 0;
                  const el = (
                    <circle
                      key={seg.key}
                      cx="40"
                      cy="40"
                      r={R}
                      fill="none"
                      stroke={seg.color}
                      strokeWidth="10"
                      strokeDasharray={`${dash} ${C - dash}`}
                      strokeDashoffset={-offset}
                      transform="rotate(-90 40 40)"
                    />
                  );
                  offset += dash;
                  return el;
                })}
              </svg>
              <div className="flex-1 space-y-1">
                {donut.map((seg) => (
                  <div key={seg.key} className="flex items-center gap-2 text-[11px]">
                    <span className="h-2 w-2 rounded-full" style={{ background: seg.color }} />
                    <span className="flex-1 text-muted-foreground">{seg.label}</span>
                    <span className="font-mono text-foreground/90">
                      {total > 0 ? Math.round((seg.value / total) * 100) : 0}٪
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* معیارها */}
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
                <p className="font-mono text-sm font-bold text-violet-300">
                  {(d.rsi_mean ?? 0).toFixed(0)}
                </p>
                <p className="text-[9px] text-muted-foreground">RSI میانگین</p>
              </div>
              <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
                <p className="font-mono text-sm font-bold text-violet-300">
                  {(d.volatility_mean ?? 0).toFixed(2)}
                </p>
                <p className="text-[9px] text-muted-foreground">نوسان</p>
              </div>
              <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
                <p className="font-mono text-sm font-bold text-violet-300">
                  {(d.trend_mean ?? 0).toFixed(2)}
                </p>
                <p className="text-[9px] text-muted-foreground">قدرت روند</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
