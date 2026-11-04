"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Activity, AlertTriangle, ArrowRight, CheckCircle2, XCircle,
  Clock, TrendingUp, TrendingDown, Minus, Info, BarChart3,
} from "lucide-react";

interface RegimeData {
  n: number;
  accuracy_pct: number | null;
}

interface PerRegime {
  all: RegimeData;
  conf_ge_70: RegimeData;
}

interface Bucket {
  range: string;
  n: number;
  accuracy_pct: number | null;
}

interface TimeframeResult {
  name: string;
  resample_hours: number;
  forward_bars: number;
  range_max_dev_pct: number;
  samples: number;
  baseline_bounded_pct: number;
  range_accuracy_pct: number;
  range_lift_vs_baseline: number;
  range_verdict: "PASS" | "FAIL";
  buckets: Bucket[];
  per_regime: {
    uptrend: PerRegime;
    downtrend: PerRegime;
    range: PerRegime;
  };
  best_high_conf_accuracy_pct: number;
  trend_verdict: "PASS" | "FAIL" | "MARGINAL";
}

interface Data {
  as_of: string;
  data_source: string;
  hypothesis: string;
  results: TimeframeResult[];
  trend_passed: number;
  range_passed: number;
  overall_verdict: string;
}

const REGIME_META = {
  uptrend: { label: "صعودی", icon: TrendingUp, color: "emerald" },
  downtrend: { label: "نزولی", icon: TrendingDown, color: "rose" },
  range: { label: "رنج", icon: Minus, color: "amber" },
};

function VerdictBadge({ verdict }: { verdict: "PASS" | "FAIL" | "MARGINAL" }) {
  if (verdict === "PASS") {
    return (
      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/40">
        <CheckCircle2 className="h-3 w-3 mr-1" /> PASS
      </Badge>
    );
  }
  if (verdict === "MARGINAL") {
    return (
      <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/40">
        <Minus className="h-3 w-3 mr-1" /> MARGINAL
      </Badge>
    );
  }
  return (
    <Badge className="bg-rose-500/20 text-rose-400 border-rose-500/40">
      <XCircle className="h-3 w-3 mr-1" /> FAIL
    </Badge>
  );
}

function AccuracyBar({ value, baseline }: { value: number | null; baseline?: number }) {
  if (value === null) return <span className="text-muted-foreground">—</span>;
  const pct = Math.max(0, Math.min(100, value));
  const color =
    pct >= 60 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-muted/30 rounded h-2 relative overflow-hidden">
        <div className={`${color} h-full`} style={{ width: `${pct}%` }} />
        {baseline !== undefined && (
          <div
            className="absolute top-0 bottom-0 w-px bg-foreground/50"
            style={{ left: `${baseline}%` }}
            title={`Baseline: ${baseline.toFixed(1)}%`}
          />
        )}
      </div>
      <span className="font-mono text-xs w-12 text-left">{pct.toFixed(1)}%</span>
    </div>
  );
}

function TimeframeCard({ tf }: { tf: TimeframeResult }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            {tf.name}
          </CardTitle>
          <div className="flex gap-2">
            <VerdictBadge verdict={tf.trend_verdict} />
            <Badge variant="outline" className="text-xs">
              {tf.samples.toLocaleString()} samples
            </Badge>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Forward: {tf.forward_bars} bars | Range threshold: ±{tf.range_max_dev_pct}%
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Per-regime trend accuracy */}
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">
            دقت trend (با confidence ≥ 70)
          </div>
          <div className="space-y-2">
            {(["uptrend", "downtrend"] as const).map((regime) => {
              const meta = REGIME_META[regime];
              const Icon = meta.icon;
              const data = tf.per_regime[regime];
              return (
                <div key={regime} className="flex items-center gap-3">
                  <div className="flex items-center gap-1 w-20">
                    <Icon className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs">{meta.label}</span>
                  </div>
                  <div className="flex-1">
                    <AccuracyBar value={data.conf_ge_70.accuracy_pct} />
                  </div>
                  <span className="text-xs text-muted-foreground w-20 text-left font-mono">
                    n={data.conf_ge_70.n.toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Range with baseline comparison */}
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-2">
            دقت range (با baseline)
            <span className={tf.range_verdict === "PASS" ? "text-emerald-400" : "text-rose-400"}>
              ({tf.range_lift_vs_baseline > 0 ? "+" : ""}{tf.range_lift_vs_baseline}% lift)
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 w-20">
              <Minus className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs">رنج</span>
            </div>
            <div className="flex-1">
              <AccuracyBar
                value={tf.range_accuracy_pct}
                baseline={tf.baseline_bounded_pct}
              />
            </div>
            <span className="text-xs text-muted-foreground w-20 text-left font-mono">
              n={tf.per_regime.range.conf_ge_70.n.toLocaleString()}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Baseline: {tf.baseline_bounded_pct}% (any window bounded) — خط عمودی در نوار
          </p>
        </div>

        {/* Confidence buckets */}
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">
            دقت بر اساس confidence
          </div>
          <div className="space-y-1">
            {tf.buckets.map((b) => (
              <div key={b.range} className="flex items-center gap-2 text-xs">
                <span className="w-16 text-muted-foreground font-mono">{b.range}</span>
                <div className="flex-1">
                  <AccuracyBar value={b.accuracy_pct} />
                </div>
                <span className="w-20 text-muted-foreground font-mono text-left">
                  n={b.n.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function RegimeAccuracyPage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/regime-confidence-fixed.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="container py-8">
        <Card className="border-rose-500/30">
          <CardHeader>
            <CardTitle className="text-rose-400 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              خطا در بارگذاری داده
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container py-8 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            دقت تشخیص رژیم SarvRouter
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data.hypothesis}
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          Research · Insight only
        </Badge>
      </div>

      {/* Overall summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-muted-foreground">داده</div>
              <div className="text-sm font-mono">{data.data_source}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">verdict</div>
              <div className={`text-lg font-bold ${data.overall_verdict === "PASS" ? "text-emerald-400" : "text-rose-400"}`}>
                {data.overall_verdict}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Trend</div>
              <div className="text-sm font-mono">{data.trend_passed}/3 PASS</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Range</div>
              <div className="text-sm font-mono">{data.range_passed}/3 PASS</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timeframe cards */}
      <div className="grid gap-6">
        {data.results.map((tf) => (
          <TimeframeCard key={tf.name} tf={tf} />
        ))}
      </div>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2 text-xs text-amber-200/90">
            <Info className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <strong>این ابزار تحلیل است، نه سیگنال معاملاتی.</strong>{" "}
              دقت trend با confidence ≥ 70 اندازه‌گیری شده. Range با max-deviation
              (نه forward return). Baseline برای مقایسه.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-xs text-muted-foreground text-center pt-2 space-y-1">
        <p>
          as_of: <span className="font-mono">{data.as_of}</span>
        </p>
        <p>داده: {data.data_source}</p>
        <Link href="/" className="inline-flex items-center gap-1 mt-2 text-primary hover:underline">
          بازگشت <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
