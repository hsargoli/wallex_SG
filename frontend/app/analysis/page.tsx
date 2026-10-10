"use client";

import { useState } from "react";
import { Activity, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useAnalysis } from "@/lib/queries";
import type { AnalysisRegimeCounts } from "@/lib/api";
import { formatPct } from "@/lib/format";

const SYMBOLS = ["BTCTMN", "ETHTMN", "USDTTMN"] as const;
const TIMEFRAMES = ["1h"] as const;

const REGIME_LABELS: Record<string, { fa: string; color: string }> = {
  trending_up: { fa: "صعودی", color: "text-emerald-500" },
  trending_down: { fa: "نزولی", color: "text-red-500" },
  ranging: { fa: "رنج", color: "text-sky-500" },
  choppy: { fa: "پرنوسان", color: "text-amber-500" },
};

function RegimeBar({ counts, total }: { counts: AnalysisRegimeCounts; total: number }) {
  if (total === 0) return null;
  const items: Array<{ key: keyof AnalysisRegimeCounts; color: string }> = [
    { key: "trending_up", color: "bg-emerald-500" },
    { key: "ranging", color: "bg-sky-500" },
    { key: "choppy", color: "bg-amber-500" },
    { key: "trending_down", color: "bg-red-500" },
  ];
  return (
    <div className="flex h-3 overflow-hidden rounded-full bg-muted">
      {items.map(({ key, color }) => {
        const pct = (counts[key] ?? 0) / total * 100;
        if (pct === 0) return null;
        return (
          <div
            key={key}
            className={color}
            style={{ width: `${pct}%` }}
            title={`${REGIME_LABELS[key].fa}: ${pct.toFixed(1)}%`}
          />
        );
      })}
    </div>
  );
}

export default function AnalysisPage() {
  const [symbol, setSymbol] = useState<string>(SYMBOLS[0]);
  const [timeframe, setTimeframe] = useState<string>(TIMEFRAMES[0]);

  const { data, isLoading, isError } = useAnalysis(symbol, timeframe);

  return (
    <div className="space-y-6 p-6" dir="rtl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-amber-400" />
          <h1 className="text-2xl font-bold">تحلیل شخصیت ارز</h1>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="rounded-lg border border-border/50 bg-card px-3 py-1.5 text-sm"
          >
            {SYMBOLS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="rounded-lg border border-border/50 bg-card px-3 py-1.5 text-sm"
          >
            {TIMEFRAMES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {/* Status */}
      {isLoading && <div className="text-muted-foreground">در حال تحلیل…</div>}
      {isError && <div className="text-red-500">خطا در دریافت تحلیل</div>}

      {data && data.window_count > 0 && (
        <>
          {/* Regime distribution */}
          <div className="rounded-2xl border border-border/50 bg-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-medium">توزیع رژیم‌ها</span>
              <span className="text-xs text-muted-foreground">
                {data.window_count} پنجره
              </span>
            </div>
            <RegimeBar counts={data.regime_counts} total={data.window_count} />
            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.entries(data.regime_counts).map(([key, count]) => {
                const label = REGIME_LABELS[key];
                if (!label) return null;
                const pct = (count / data.window_count) * 100;
                return (
                  <div key={key} className="rounded-xl border border-border/40 p-3">
                    <div className={`text-sm font-medium ${label.color}`}>{label.fa}</div>
                    <div className="mt-1 text-xl font-bold tabular-nums">{count}</div>
                    <div className="text-xs text-muted-foreground">{pct.toFixed(1)}٪</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Stats */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-border/50 bg-card p-5">
              <div className="mb-2 text-sm text-muted-foreground">رژیم غالب</div>
              <div className="flex items-center gap-2 text-xl font-bold">
                {data.dominant_regime === "trending_up" && <TrendingUp className="h-5 w-5 text-emerald-500" />}
                {data.dominant_regime === "trending_down" && <TrendingDown className="h-5 w-5 text-red-500" />}
                {data.dominant_regime === "ranging" && <Minus className="h-5 w-5 text-sky-500" />}
                {data.dominant_regime && REGIME_LABELS[data.dominant_regime]?.fa}
              </div>
            </div>
            <div className="rounded-2xl border border-border/50 bg-card p-5">
              <div className="mb-2 text-sm text-muted-foreground">نوسان میانگین</div>
              <div className="text-xl font-bold tabular-nums">{formatPct(data.volatility_mean)}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                انحراف: {formatPct(data.volatility_std)}
              </div>
            </div>
            <div className="rounded-2xl border border-border/50 bg-card p-5">
              <div className="mb-2 text-sm text-muted-foreground">RSI میانگین</div>
              <div className="text-xl font-bold tabular-nums">{data.rsi_mean.toFixed(1)}</div>
            </div>
            <div className="rounded-2xl border border-border/50 bg-card p-5">
              <div className="mb-2 text-sm text-muted-foreground">قدرت روند</div>
              <div className="text-xl font-bold tabular-nums">{data.trend_mean.toFixed(2)}</div>
            </div>
          </div>
        </>
      )}

      {data && data.window_count === 0 && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-5 text-sm">
          داده کافی برای تحلیل وجود ندارد. (کندل‌ها: ۰)
        </div>
      )}
    </div>
  );
}
