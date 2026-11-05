"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Play, AlertTriangle, TrendingUp, TrendingDown, Minus, Info,
  ArrowRight, CheckCircle2, XCircle, Loader2,
} from "lucide-react";

interface BacktestResult {
  switches: number;
  accuracy: number;
  total_signals: number;
  correct: number;
}

interface BacktestResponse {
  default: BacktestResult;
  custom: BacktestResult;
  delta: { accuracy: number; switches_pct: number };
  warnings: string[];
}

const DEFAULTS = {
  stability_window: 36,
  cooldown_candles: 12,
  uptrend_adx_min: 25,
  downtrend_adx_min: 25,
  cash_reserve_pct: 10,
  daily_loss_limit_pct: 2,
};

export default function SarvRouterBuilderPage() {
  const [params, setParams] = useState(DEFAULTS);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateParam = (key: keyof typeof DEFAULTS, value: number) => {
    setParams((p) => ({ ...p, [key]: value }));
  };

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/backend/v1/sarvrouter/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: BacktestResponse = await res.json();
      setResult(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const deltaColor = (d: number) => {
    if (d > 0) return "text-emerald-400";
    if (d < 0) return "text-rose-400";
    return "text-muted-foreground";
  };
  const deltaBadge = (d: number) => {
    if (d > 0) return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/40">بهتر</Badge>;
    if (d < 0) return <Badge className="bg-rose-500/20 text-rose-400 border-rose-500/40">بدتر</Badge>;
    return <Badge variant="outline">بدون تغییر</Badge>;
  };

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Play className="h-6 w-6 text-primary" />
            سازنده‌ی SarvRouter
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            پارامترها را تغییر بده، دکمه‌ی اجرا را بزن، و ببین چه اتفاقی می‌افتد.
          </p>
        </div>
        <Badge variant="outline">Research · Insight only</Badge>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">تنظیمات</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "stability_window", label: "پنجره‌ی پایداری", min: 6, max: 100, step: 1, unit: "کندل" },
            { key: "cooldown_candles", label: "Cooldown", min: 3, max: 50, step: 1, unit: "کندل" },
            { key: "uptrend_adx_min", label: "حداقل ADX برای صعودی", min: 15, max: 40, step: 1, unit: "" },
            { key: "downtrend_adx_min", label: "حداقل ADX برای نزولی", min: 15, max: 40, step: 1, unit: "" },
            { key: "cash_reserve_pct", label: "ذخیره‌ی نقدی", min: 0, max: 30, step: 1, unit: "%" },
            { key: "daily_loss_limit_pct", label: "حد ضرر روزانه", min: 1, max: 10, step: 0.5, unit: "%" },
          ].map(({ key, label, min, max, step, unit }) => (
            <div key={key} className="flex flex-col gap-1">
              <div className="flex justify-between text-sm">
                <span>{label}</span>
                <span className="font-mono text-muted-foreground">
                  {params[key as keyof typeof DEFAULTS]}{unit}
                </span>
              </div>
              <input
                type="range"
                min={min} max={max} step={step}
                value={params[key as keyof typeof DEFAULTS]}
                onChange={(e) => updateParam(key as keyof typeof DEFAULTS, Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Button onClick={runBacktest} disabled={loading} className="flex-1">
              {loading ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />در حال اجرا...</> : <><Play className="h-4 w-4 mr-2" />اجرای تست</>}
            </Button>
            <Button variant="outline" onClick={() => setParams(DEFAULTS)}>بازنشانی</Button>
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-rose-500/30">
          <CardContent className="pt-4 flex items-center gap-2 text-sm text-rose-400">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle className="text-base">Default (پیش‌فرض)</CardTitle></CardHeader>
              <CardContent>
                <div className="text-3xl font-bold font-mono">{result.default.accuracy}%</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {result.default.correct}/{result.default.total_signals} سیگنال درست
                </div>
                <div className="text-xs text-muted-foreground mt-2">
                  switch: {result.default.switches}
                </div>
              </CardContent>
            </Card>
            <Card className="border-primary/40">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Custom (شما)</CardTitle>
                  {deltaBadge(result.delta.accuracy)}
                </div>
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold font-mono ${deltaColor(result.delta.accuracy)}`}>
                  {result.custom.accuracy}%
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {result.custom.correct}/{result.custom.total_signals} سیگنال درست
                </div>
                <div className="text-xs text-muted-foreground mt-2">
                  switch: {result.custom.switches} ({result.delta.switches_pct > 0 ? "+" : ""}{result.delta.switches_pct}%)
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Delta summary */}
          <Card>
            <CardContent className="pt-4 flex flex-wrap items-center gap-4">
              <span className="text-sm">اختلاف با Default:</span>
              <span className={`text-lg font-bold font-mono ${deltaColor(result.delta.accuracy)}`}>
                {result.delta.accuracy > 0 ? "+" : ""}{result.delta.accuracy}%
              </span>
              <span className="text-xs text-muted-foreground">
                {result.delta.accuracy > 0 ? "بهتر از پیش‌فرض" : result.delta.accuracy < 0 ? "بدتر از پیش‌فرض" : "بدون تغییر"}
              </span>
            </CardContent>
          </Card>

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <Card className="border-amber-500/30 bg-amber-500/5">
              <CardContent className="pt-4">
                {result.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-amber-200/90">
                    <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                    <span>{w}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Info */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2 text-xs text-amber-200/90">
            <Info className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <strong>این یک ابزار آزمایشی است.</strong> نتایج فقط برای BTCUSDT (۵.۸ سال) معتبر است.
              این backtest روی داده‌های گذشته اجرا می‌شود — نه پیش‌بینی آینده. تصمیم نهایی با شماست.
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-xs text-muted-foreground text-center">
        <Link href="/" className="inline-flex items-center gap-1 text-primary hover:underline">
          بازگشت <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
