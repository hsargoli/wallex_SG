"use client";

import { TrendingDown, Activity, Zap, BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface ScannerStats {
  oversold: number;     // RSI < 30
  macdBullish: number;  // macd_hist > 0
  bbLower: number;      // bb_pct < 20
  volatile: number;     // atr_pct > 2
  total: number;
}

interface ScannerKPIProps {
  stats: ScannerStats;
}

export function ScannerKPI({ stats }: ScannerKPIProps) {
  const pct = (n: number) => (stats.total > 0 ? (n / stats.total) * 100 : 0);
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <KpiCard label="اشباع فروش (RSI<30)" value={stats.oversold} pct={pct(stats.oversold)} icon={TrendingDown} tone="emerald" />
      <KpiCard label="MACD مثبت" value={stats.macdBullish} pct={pct(stats.macdBullish)} icon={Activity} tone="emerald" />
      <KpiCard label="نزدیک کف باند" value={stats.bbLower} pct={pct(stats.bbLower)} icon={Zap} tone="blue" />
      <KpiCard label="پرنوسان (ATR>2%)" value={stats.volatile} pct={pct(stats.volatile)} icon={BarChart3} tone="amber" />
    </div>
  );
}

const TONES = {
  emerald: { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  blue:    { text: "text-blue-400",    bg: "bg-blue-500/10",    border: "border-blue-500/20" },
  amber:   { text: "text-amber-400",   bg: "bg-amber-500/10",   border: "border-amber-500/20" },
} as const;

function KpiCard({ label, value, pct, icon: Icon, tone }: {
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
          <p className={cn("mt-1 font-mono text-2xl font-bold", t.text)}>{value}</p>
          {pct !== undefined && (
            <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{pct.toFixed(0)}%</p>
          )}
        </div>
        <Icon className={cn("h-8 w-8 opacity-40", t.text)} />
      </CardContent>
    </Card>
  );
}
