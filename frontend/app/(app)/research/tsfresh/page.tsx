"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Activity, Clock, AlertTriangle, BarChart3, ArrowRight } from "lucide-react";

interface SimilarPeriod {
  date: string;
  similarity: number;
  forward_return_24h_pct: number;
}

interface Stats {
  n: number;
  mean_return_24h_pct: number;
  median_return_24h_pct: number;
  std_return_24h_pct: number;
  positive_pct: number;
  min_return_24h_pct: number;
  max_return_24h_pct: number;
}

interface SimilarityData {
  as_of: string;
  current_datetime: string;
  current_price: number;
  current_regime: string;
  window_hours: number;
  horizon_hours: number;
  n_features: number;
  feature_names: string[];
  current_features: Record<string, number | null>;
  similar_periods: SimilarPeriod[];
  stats: Stats;
  disclaimer: string;
}

const FEATURE_LABELS: Record<string, string> = {
  ret_1_mean: "میانگین بازده ۱h",
  ret_1_std: "انحراف معیار بازده ۱h",
  ret_24: "بازده ۲۴h",
  rsi_14_mean: "میانگین RSI(14)",
  rsi_14_last: "آخرین RSI(14)",
  atr_14_mean: "میانگین ATR(14)",
  atr_14_std: "انحراف معیار ATR(14)",
  atr_pct_mean: "ATR% میانگین",
  ema_ratio_mean: "نسبت EMA20/EMA50",
  macd_mean: "میانگین MACD",
  macd_hist_mean: "میانگین MACD Histogram",
  vol_ratio_mean: "نسبت حجم به میانگین",
  vol_ratio_std: "انحراف معیار نسبت حجم",
  volatility: "نوسان‌پذیری",
  close_position: "موقعیت close در دامنه",
  hh_ll_ratio: "نسبت High-Low به Close",
  upper_wick_mean: "میانگین سایه بالایی",
  lower_wick_mean: "میانگین سایه پایینی",
  body_ratio_mean: "میانگین نسبت بدنه",
};

function formatPct(v: number, digits = 2): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("fa-IR", { year: "numeric", month: "2-digit", day: "2-digit" });
  } catch {
    return iso.slice(0, 10);
  }
}

export default function TSFreshResearchPage() {
  const [data, setData] = useState<SimilarityData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/similarity.json")
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

  const { stats } = data;
  const meanPositive = stats.mean_return_24h_pct > 0;
  const positiveColor = stats.positive_pct >= 55 ? "text-emerald-400" : stats.positive_pct >= 45 ? "text-amber-400" : "text-rose-400";

  // histogram buckets: 5 buckets for -5% to +5%
  const buckets = [
    { label: "< -3%", min: -Infinity, max: -3, count: 0, color: "bg-rose-500/70" },
    { label: "-3% → -1%", min: -3, max: -1, count: 0, color: "bg-rose-400/70" },
    { label: "-1% → +1%", min: -1, max: 1, count: 0, color: "bg-slate-400/70" },
    { label: "+1% → +3%", min: 1, max: 3, count: 0, color: "bg-emerald-400/70" },
    { label: "> +3%", min: 3, max: Infinity, count: 0, color: "bg-emerald-500/70" },
  ];
  data.similar_periods.forEach((p) => {
    const v = p.forward_return_24h_pct;
    const b = buckets.find((bk) => v >= bk.min && v < bk.max);
    if (b) b.count += 1;
  });
  const maxCount = Math.max(...buckets.map((b) => b.count), 1);

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            تحلیل تشابه تاریخی BTC
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            الگوی ۲۴ ساعت اخیر BTC، با ۵ سال گذشته مقایسه می‌شود.
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          Research · Insight only
        </Badge>
      </div>

      {/* Meta card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground text-xs mb-1">آخرین داده</div>
              <div className="font-mono text-xs">{data.current_datetime}</div>
            </div>
            <div>
              <div className="text-muted-foreground text-xs mb-1">قیمت</div>
              <div className="font-mono">${data.current_price.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground text-xs mb-1">پنجره</div>
              <div>{data.window_hours}h الگو</div>
            </div>
            <div>
              <div className="text-muted-foreground text-xs mb-1">افق پیش‌بینی</div>
              <div>{data.horizon_hours}h آینده</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 1: Current Pattern */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" />
            ۱. الگوی فعلی
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {data.feature_names.map((f) => {
              const v = data.current_features[f];
              return (
                <div key={f} className="border rounded-lg p-2 bg-muted/20">
                  <div className="text-xs text-muted-foreground truncate" title={FEATURE_LABELS[f] ?? f}>
                    {FEATURE_LABELS[f] ?? f}
                  </div>
                  <div className="font-mono text-sm mt-0.5">
                    {v === null ? "—" : Number.isInteger(v) ? v : v.toFixed(4)}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Similar Periods */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            ۲. {data.similar_periods.length} دوره‌ی مشابه تاریخی
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted-foreground border-b">
                  <th className="text-right py-2 font-normal">#</th>
                  <th className="text-right py-2 font-normal">تاریخ</th>
                  <th className="text-left py-2 font-normal">شباهت</th>
                  <th className="text-left py-2 font-normal">بازده ۲۴h بعد</th>
                </tr>
              </thead>
              <tbody>
                {data.similar_periods.slice(0, 15).map((p, i) => {
                  const positive = p.forward_return_24h_pct >= 0;
                  return (
                    <tr key={`${p.date}-${i}`} className="border-b border-border/30">
                      <td className="py-2 text-right text-muted-foreground">{i + 1}</td>
                      <td className="py-2 text-right font-mono text-xs">{formatDate(p.date)}</td>
                      <td className="py-2 text-left font-mono">{(p.similarity * 100).toFixed(1)}%</td>
                      <td className={`py-2 text-left font-mono ${positive ? "text-emerald-400" : "text-rose-400"}`}>
                        {formatPct(p.forward_return_24h_pct)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {data.similar_periods.length > 15 && (
            <p className="text-xs text-muted-foreground mt-3 text-center">
              ۱۵ مورد از {data.similar_periods.length} نمایش داده شده
            </p>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Forward Returns Stats + Histogram */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            ۳. بازده ۲۴h بعد از الگوهای مشابه
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="border rounded-lg p-3">
              <div className="text-xs text-muted-foreground">میانگین</div>
              <div className={`font-mono text-lg ${meanPositive ? "text-emerald-400" : "text-rose-400"}`}>
                {formatPct(stats.mean_return_24h_pct)}
              </div>
            </div>
            <div className="border rounded-lg p-3">
              <div className="text-xs text-muted-foreground">میانه</div>
              <div className={`font-mono text-lg ${stats.median_return_24h_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {formatPct(stats.median_return_24h_pct)}
              </div>
            </div>
            <div className="border rounded-lg p-3">
              <div className="text-xs text-muted-foreground">درصد مثبت</div>
              <div className={`font-mono text-lg ${positiveColor}`}>{stats.positive_pct.toFixed(1)}%</div>
            </div>
            <div className="border rounded-lg p-3">
              <div className="text-xs text-muted-foreground">تعداد (N)</div>
              <div className="font-mono text-lg">{stats.n}</div>
            </div>
          </div>

          {/* Histogram */}
          <div>
            <div className="text-xs text-muted-foreground mb-2">توزیع بازده</div>
            <div className="space-y-1.5">
              {buckets.map((b) => (
                <div key={b.label} className="flex items-center gap-2 text-xs">
                  <span className="w-20 text-muted-foreground text-left font-mono">{b.label}</span>
                  <div className="flex-1 bg-muted/30 rounded h-5 relative overflow-hidden">
                    <div
                      className={`${b.color} h-full rounded transition-all`}
                      style={{ width: `${(b.count / maxCount) * 100}%` }}
                    />
                  </div>
                  <span className="w-8 text-right font-mono text-muted-foreground">{b.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Min/Max */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">حداقل:</span>
              <span className="font-mono text-rose-400">{formatPct(stats.min_return_24h_pct)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">حداکثر:</span>
              <span className="font-mono text-emerald-400">{formatPct(stats.max_return_24h_pct)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2 text-xs text-amber-200/90">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <strong>هشدار:</strong> این یک ابزار تحلیل تاریخی است، نه سیگنال معاملاتی. الگوهای گذشته ممکن است تکرار نشوند. هزینه‌ی round-trip معامله (۰.۶۵٪) در این تحلیل لحاظ نشده است.
              {stats.mean_return_24h_pct < 0.65 && (
                <span className="block mt-1">
                  ⚠️ میانگین بازده ({stats.mean_return_24h_pct.toFixed(2)}%) کمتر از هزینه‌ی معامله (۰.۶۵٪) است.
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-xs text-muted-foreground text-center pt-2">
        <p>
          as_of: <span className="font-mono">{data.as_of}</span>
        </p>
        <p className="mt-1">
          داده: BTCUSDT (Binance) · {data.n_features} feature · {data.similar_periods.length} match (N&gt;30, AP-58)
        </p>
        <Link href="/" className="inline-flex items-center gap-1 mt-2 text-primary hover:underline">
          بازگشت <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
