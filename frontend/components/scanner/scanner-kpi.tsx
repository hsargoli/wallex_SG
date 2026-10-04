"use client";

import { TrendingUp, TrendingDown, Minus, BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface ScannerStats {
  bullish: number;
  bearish: number;
  neutral: number;
  total: number;
}

interface ScannerKPIProps {
  stats: ScannerStats;
}

export function ScannerKPI({ stats }: ScannerKPIProps) {
  const buyPct = stats.total > 0 ? (stats.bullish / stats.total) * 100 : 0;
  const sellPct = stats.total > 0 ? (stats.bearish / stats.total) * 100 : 0;
  const holdPct = stats.total > 0 ? (stats.neutral / stats.total) * 100 : 0;

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <KpiCard
        label="صعودی"
        value={stats.bullish}
        pct={buyPct}
        icon={TrendingUp}
        tone="emerald"
      />
      <KpiCard
        label="نزولی"
        value={stats.bearish}
        pct={sellPct}
        icon={TrendingDown}
        tone="red"
      />
      <KpiCard
        label="بدون روند"
        value={stats.neutral}
        pct={holdPct}
        icon={Minus}
        tone="zinc"
      />
      <KpiCard
        label="کل نمادها"
        value={stats.total}
        icon={BarChart3}
        tone="blue"
      />
    </div>
  );
}

const TONES = {
  emerald: {
    text: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
  },
  red: {
    text: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
  },
  zinc: {
    text: "text-zinc-400",
    bg: "bg-zinc-500/10",
    border: "border-zinc-500/20",
  },
  blue: {
    text: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
} as const;

function KpiCard({
  label,
  value,
  pct,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  pct?: number;
  icon: React.ComponentType<{ className?: string }>;
  tone: keyof typeof TONES;
}) {
  const t = TONES[tone];
  return (
    <Card className={cn("border", t.border, t.bg)}>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className={cn("mt-1 font-mono text-2xl font-bold", t.text)}>
            {value}
          </p>
          {pct !== undefined && (
            <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
              {pct.toFixed(0)}%
            </p>
          )}
        </div>
        <Icon className={cn("h-8 w-8 opacity-40", t.text)} />
      </CardContent>
    </Card>
  );
}
