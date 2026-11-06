"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Play, AlertTriangle, Info, ArrowRight, Loader2,
  Settings2, Shield, Activity, BrainCircuit, Route
} from "lucide-react";
import { cn } from "@/lib/utils";

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

  const isBetter = result ? result.delta.accuracy > 0 : false;
  const isWorse = result ? result.delta.accuracy < 0 : false;

  return (
    <div className="container py-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings2 className="h-6 w-6 text-primary" />
            آزمایشگاه SarvRouter
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            تنظیمات مغز متفکر ربات‌ها را تغییر بده و ببین در گذشته چه نتیجه‌ای می‌گرفتی.
          </p>
        </div>
        <Badge variant="outline">Research · Insight only</Badge>
      </div>

      {/* Educational Intro */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="pt-6 space-y-4 text-sm leading-relaxed">
          <div className="flex items-start gap-3">
            <BrainCircuit className="h-6 w-6 text-primary shrink-0" />
            <div>
              <strong className="text-base text-primary">SarvRouter کیست و چه می‌کند؟</strong>
              <p className="text-muted-foreground mt-1">
                SarvRouter یک ربات معامله‌گر نیست، بلکه یک <strong>«مسیریاب» (Navigator)</strong> است. 
                وظیفه او این است که به بازار نگاه کند و تشخیص دهد که بازار در چه حالتی است: 
                <strong> صعودی (Uptrend)</strong>، <strong>نزولی (Downtrend)</strong> یا <strong>رنج (Range)</strong>. 
                سپس بر اساس این تشخیص، تصمیم می‌گیرد که کدام ربات معامله‌گر (مثل Nooaah) وارد عمل شود یا سرمایه در امان بماند.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Route className="h-6 w-6 text-primary shrink-0" />
            <div>
              <strong className="text-base text-primary">چرا اینجا هستیم؟</strong>
              <p className="text-muted-foreground mt-1">
                تشخیص روند بازار کار سختی است. اگر ربات بیش از حد حساس باشد، مدام سیگنال‌های اشتباه (Noise) می‌گیرد و ضرر می‌کند. 
                اگر بیش از حد محتاط باشد، فرصت‌های سود را از دست می‌دهد. 
                در این آزمایشگاه، می‌توانید <strong>«آستانه‌های حساسیت»</strong> ربات را تغییر دهید و ببینید 
                در شبیه‌سازی یک‌ساله‌ی گذشته (داده‌های واقعی بیت‌کوین)، کدام تنظیمات بهترین دقت را داشته است.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Form Groups */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Trend Detection Group */}
        <Card>
          <CardHeader className="pb-3 border-b border-border/50 mb-4">
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="h-5 w-5 text-emerald-400" />
              تنظیمات تشخیص روند
            </CardTitle>
            <CardDescription>ربات چگونه بفهمد بازار صعودی است یا نزولی؟</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {[
              { key: "stability_window", label: "پنجره پایداری", desc: "روند باید چند ساعت ثابت بماند تا تأیید شود؟ (عدد بالاتر = محتاط‌تر)", recommended: "معمول: ۲۴ تا ۴۸", min: 6, max: 100, step: 1, unit: "ساعت" },
              { key: "cooldown_candles", label: "زمان خنک‌شدن", desc: "بعد از تغییر روند، چند ساعت صبر کند تا دوباره وارد شود؟", recommended: "معمول: ۶ تا ۱۲", min: 3, max: 50, step: 1, unit: "ساعت" },
              { key: "uptrend_adx_min", label: "قدرت روند صعودی (ADX)", desc: "حداقل قدرت لازم برای تشخیص صعود. (بالاتر = فقط روندهای قوی)", recommended: "معمول: ۲۵ تا ۳۰", min: 15, max: 40, step: 1, unit: "" },
              { key: "downtrend_adx_min", label: "قدرت روند نزولی (ADX)", desc: "حداقل قدرت لازم برای تشخیص نزول. (بالاتر = فقط روندهای قوی)", recommended: "معمول: ۲۵ تا ۳۰", min: 15, max: 40, step: 1, unit: "" },
            ].map(({ key, label, desc, recommended, min, max, step, unit }) => (
              <div key={key} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">{label}</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min={min} max={max} step={step}
                      value={params[key as keyof typeof DEFAULTS]}
                      onChange={(e) => updateParam(key as keyof typeof DEFAULTS, Number(e.target.value))}
                      className="w-20 bg-background border border-border rounded-md px-2 py-1 text-sm text-center font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                    <span className="text-xs text-muted-foreground w-8">{unit}</span>
                  </div>
                </div>
                <div className="flex justify-between items-start gap-2">
                  <p className="text-[11px] text-muted-foreground leading-tight">{desc}</p>
                  <span className="text-[10px] font-medium text-emerald-500/80 bg-emerald-500/10 px-2 py-0.5 rounded-full whitespace-nowrap">{recommended}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Risk Management Group */}
        <Card>
          <CardHeader className="pb-3 border-b border-border/50 mb-4">
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="h-5 w-5 text-amber-400" />
              مدیریت ریسک
            </CardTitle>
            <CardDescription>ربات چگونه از سرمایه شما محافظت کند؟</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {[
              { key: "cash_reserve_pct", label: "ذخیره نقدی", desc: "چند درصد از سرمایه همیشه به صورت نقد (دست نخورده) بماند؟", recommended: "معمول: ۱۰ تا ۲۰", min: 0, max: 30, step: 1, unit: "%" },
              { key: "daily_loss_limit_pct", label: "حد ضرر روزانه", desc: "اگر ضرر امروز به این درصد رسید، ربات تا فردا خاموش شود.", recommended: "معمول: ۲ تا ۳", min: 1, max: 10, step: 0.5, unit: "%" },
            ].map(({ key, label, desc, recommended, min, max, step, unit }) => (
              <div key={key} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">{label}</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min={min} max={max} step={step}
                      value={params[key as keyof typeof DEFAULTS]}
                      onChange={(e) => updateParam(key as keyof typeof DEFAULTS, Number(e.target.value))}
                      className="w-20 bg-background border border-border rounded-md px-2 py-1 text-sm text-center font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                    <span className="text-xs text-muted-foreground w-8">{unit}</span>
                  </div>
                </div>
                <div className="flex justify-between items-start gap-2">
                  <p className="text-[11px] text-muted-foreground leading-tight">{desc}</p>
                  <span className="text-[10px] font-medium text-emerald-500/80 bg-emerald-500/10 px-2 py-0.5 rounded-full whitespace-nowrap">{recommended}</span>
                </div>
              </div>
            ))}
            
            <div className="pt-6 mt-auto">
              <Button onClick={runBacktest} disabled={loading} className="w-full h-14 text-base shadow-lg shadow-primary/20">
                {loading ? <><Loader2 className="h-5 w-5 animate-spin mr-2" />در حال شبیه‌سازی...</> : <><Play className="h-5 w-5 mr-2" />شبیه‌سازی و مشاهده نتیجه</>}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error */}
      {error && (
        <Card className="border-rose-500/30 bg-rose-500/5">
          <CardContent className="pt-4 flex items-center gap-2 text-sm text-rose-400">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6 pt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="text-center space-y-2">
            <h2 className="text-xl font-bold">نتیجه شبیه‌سازی</h2>
            <p className="text-sm text-muted-foreground">مقایسه تنظیمات شما با تنظیمات پیش‌فرض کارخانه</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            {/* Default Card */}
            <Card className="opacity-70 scale-95 bg-muted/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-center text-muted-foreground">Default (پیش‌فرض)</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <div className="text-2xl font-bold font-mono text-muted-foreground">{result.default.accuracy}%</div>
                <div className="text-xs text-muted-foreground mt-1">دقت تشخیص</div>
                <div className="text-xs text-muted-foreground mt-2 border-t border-border/50 pt-2">{result.default.switches} تغییر روند</div>
              </CardContent>
            </Card>

            {/* Delta Card (Center) */}
            <div className="flex flex-col items-center justify-center p-4">
              <ArrowRight className="h-8 w-8 text-muted-foreground/30 mb-2" />
              <div className={cn(
                "px-5 py-2.5 rounded-full font-bold text-xl font-mono border shadow-sm",
                isBetter ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" :
                isWorse ? "bg-rose-500/10 text-rose-400 border-rose-500/30" :
                "bg-muted text-muted-foreground border-border"
              )}>
                {result.delta.accuracy > 0 ? "+" : ""}{result.delta.accuracy}%
              </div>
              <p className={cn(
                "text-xs font-medium mt-2 px-3 py-1 rounded-full",
                isBetter ? "text-emerald-400" : isWorse ? "text-rose-400" : "text-muted-foreground"
              )}>
                {isBetter ? "بهتر از پیش‌فرض" : isWorse ? "بدتر از پیش‌فرض" : "بدون تغییر"}
              </p>
            </div>

            {/* Custom Card */}
            <Card className="border-primary/50 shadow-xl shadow-primary/10 scale-105 bg-background">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-center text-primary font-bold">Custom (شما)</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <div className="text-4xl font-bold font-mono text-primary">{result.custom.accuracy}%</div>
                <div className="text-xs text-muted-foreground mt-1">دقت تشخیص</div>
                <div className="text-xs text-muted-foreground mt-2 border-t border-primary/20 pt-2">{result.custom.switches} تغییر روند</div>
              </CardContent>
            </Card>
          </div>

          {/* Explanation */}
          <div className="bg-muted/30 rounded-lg p-4 text-sm text-center border border-border/50">
            {isBetter && <span className="text-emerald-400">🎉 آفرین! تنظیمات شما در شبیه‌سازی یک‌ساله، عملکرد بهتری نسبت به تنظیمات پیش‌فرض داشته است.</span>}
            {isWorse && <span className="text-rose-400">⚠️ تنظیمات شما باعث شده دقت کاهش پیدا کند. شاید بهتر است پارامترها را کمی به سمت پیش‌فرض برگردانید.</span>}
            {!isBetter && !isWorse && <span className="text-muted-foreground">تنظیمات شما دقیقاً همان نتیجه پیش‌فرض را داده است.</span>}
          </div>

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <Card className="border-amber-500/30 bg-amber-500/5">
              <CardContent className="pt-4">
                {result.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-amber-200/90 mb-1 last:mb-0">
                    <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                    <span>{w}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <div className="text-xs text-muted-foreground text-center pt-8">
        <Link href="/" className="inline-flex items-center gap-1 text-primary hover:underline">
          بازگشت به داشبورد <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
