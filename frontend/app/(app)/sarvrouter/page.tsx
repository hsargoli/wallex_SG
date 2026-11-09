"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  ExternalLink,
  ShieldAlert,
  Wallet,
  Loader2,
  RefreshCw,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  HelpCircle,
  CheckCircle2,
  XCircle,
  Info,
  BrainCircuit,
  Bitcoin,
  Calendar,
  Clock,
  Play,
  LineChart
} from "lucide-react";
import {
  useSarvRouterStatus,
  useSarvRouterWhy,
  useSarvRouterFeedback,
  useSarvRouterSimulate,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";

const REGIME_FA: Record<string, { label: string; icon: any; color: string }> = {
  uptrend: { label: "صعودی", icon: TrendingUp, color: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  downtrend: { label: "نزولی", icon: TrendingDown, color: "bg-rose-500/15 text-rose-300 border-rose-500/30" },
  range: { label: "رنج (خنثی)", icon: Minus, color: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  unknown: { label: "نامشخص", icon: HelpCircle, color: "bg-slate-500/15 text-slate-300 border-slate-500/30" },
};

const ACTION_FA: Record<string, string> = {
  switched: "ورود به معامله (تغییر روند)",
  pending: "در انتظار تثبیت روند",
  no_change: "ادامه روند فعلی",
  cooldown: "استراحت کوتاه (جلوگیری از نوسان)",
};

export default function SarvRouterPage() {
  const status = useSarvRouterStatus();
  const why = useSarvRouterWhy();
  const feedback = useSarvRouterFeedback();
  const simulate = useSarvRouterSimulate();
  
  // Playground State
  const [simTf, setSimTf] = useState("1h");
  const [simDate, setSimDate] = useState("2026-10-01");
  const [simResult, setSimResult] = useState<any>(null);

  const handleSimulate = () => {
    setSimResult(null);
    simulate.mutate(
      { symbol: "BTCUSDT", date: simDate, timeframe: simTf },
      {
        onSuccess: (data) => setSimResult(data),
        onError: (err: any) => {
          let msg = "خطا در اجرای شبیه‌سازی";
          if (err.response?.data?.detail) {
            if (typeof err.response.data.detail === 'string') {
              msg = err.response.data.detail;
            } else if (Array.isArray(err.response.data.detail)) {
              msg = "اطلاعات ورودی نامعتبر است. لطفاً تاریخ را بررسی کنید.";
            }
          }
          setSimResult({ error: msg });
        }
      }
    );
  };

  if (status.isLoading) {
    return (
      <div className="container max-w-5xl py-8 space-y-4">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (status.isError || !status.data) {
    return (
      <div className="container max-w-5xl py-8">
        <Card className="border-rose-500/30 bg-rose-500/5">
          <CardHeader>
            <CardTitle className="text-rose-400">خطا در ارتباط با دستیار</CardTitle>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => status.refetch()}>
              <RefreshCw className="h-4 w-4 ml-2" /> تلاش دوباره
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const d = status.data as any;
  const last = d.last_decision;
  const regime = REGIME_FA[d.regime] || REGIME_FA.unknown;
  const RegimeIcon = regime.icon;

  return (
    <div className="container max-w-5xl py-8 space-y-8">
      
      {/* ONBOARDING SECTION */}
      <div className="space-y-4">
        <div className="flex items-start justify-between border-b border-border/50 pb-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2 text-foreground">
              <BrainCircuit className="h-8 w-8 text-violet-500" />
              دستیار معامله‌گر هوشمند (Copilot)
            </h1>
            <p className="text-sm text-muted-foreground mt-3 leading-relaxed max-w-3xl text-justify">
              به سروباتس خوش آمدید. من یک ربات معامله‌گر خودکار نیستم. من یک <b>دستیار تحلیل‌گر</b> هستم. 
              میلیون‌ها داده و کندل را بررسی می‌کنم تا روند بازار را تشخیص دهم. سپس با ارائه دلایل شفاف، به شما پیشنهاد می‌دهم. 
              <b> تصمیم نهایی و مدیریت سرمایه کاملاً در اختیار شماست.</b>
            </p>
          </div>
          <Link href="/bots/sarv_router" className="hidden md:flex text-xs text-muted-foreground hover:text-violet-400 items-center gap-1 mt-2">
            نمای کلی <ExternalLink className="h-3 w-3" />
          </Link>
        </div>

        <Card className="bg-secondary/30 border-border/50">
          <CardContent className="p-4 flex flex-col md:flex-row gap-4 text-xs text-muted-foreground">
            <div className="flex-1 flex items-start gap-2">
              <Info className="h-4 w-4 text-violet-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <b>چطور روند را تشخیص می‌دهم؟</b> من از ترکیب شاخص‌های قدرت روند (ADX) و میانگین‌های متحرک (EMA) استفاده می‌کنم. وقتی ADX از حد آستانه (معمولاً ۲۵) عبور کند و EMAها به درستی مرتب شوند، یعنی روند شکل گرفته است.
              </p>
            </div>
            <div className="flex-1 flex items-start gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <b>نکته مهم درباره کارمزد:</b> صرافی‌ها برای هر خرید و فروش یک درصد کمی کارمزد برمی‌دارند. لطفاً قبل از ورود، به این هزینه‌های پنهان توجه کنید تا سود شما تحت تاثیر قرار نگیرد.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* HERO CARD */}
      <Card className="border-2 border-violet-500/30 bg-gradient-to-b from-violet-500/10 to-transparent">
        <CardContent className="p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
          
          <div className="space-y-4 text-center md:text-right w-full">
            <div className="flex flex-col items-center md:items-start gap-1">
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-1">
                <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/30 px-3 py-1">
                  <Bitcoin className="h-4 w-4 ml-1" /> بیت‌کوین (BTCTMN)
                </Badge>
                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 px-3 py-1">
                  تایم‌فریم: ۱ ساعته
                </Badge>
                <Badge variant="outline" className={`px-3 py-1 ${regime.color}`}>
                  <RegimeIcon className="h-4 w-4 ml-1" />
                  وضعیت: {regime.label}
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                * در حال حاضر تنها بیت‌کوین تحلیل می‌شود. ارزهای دیگر به‌زودی اضافه خواهند شد.
              </p>
            </div>
            
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-1">تحلیل و پیشنهاد فعلی من:</p>
              <h2 className="text-2xl font-bold text-foreground">
                {last ? ACTION_FA[last.action] || last.action : "در حال پردازش داده‌ها..."}
              </h2>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full md:w-auto shrink-0">
            <p className="text-xs text-muted-foreground text-center mb-1">نظر شما در مورد این تحلیل چیست؟</p>
            <Button 
              className="w-full md:w-48 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 h-12 text-base"
              onClick={() => feedback.mutate({ tick_id: last.tick_id, choice: "accept" })}
              disabled={!last || feedback.isPending || feedback.isSuccess}
            >
              <CheckCircle2 className="h-5 w-5 ml-2" /> تایید تحلیل
            </Button>
            <Button 
              className="w-full md:w-48 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/30 h-12 text-base"
              onClick={() => feedback.mutate({ tick_id: last.tick_id, choice: "reject" })}
              disabled={!last || feedback.isPending || feedback.isSuccess}
            >
              <XCircle className="h-5 w-5 ml-2" /> رد کردن
            </Button>
            {feedback.isSuccess && (
              <p className="text-xs text-emerald-400 text-center mt-1">بازخورد شما ثبت شد.</p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        
        {/* WHY CARD */}
        <Card className="h-full flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-violet-400" /> چرا این تصمیم را گرفتم؟
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 flex-1">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">میزان اطمینان من به این تحلیل:</span>
                <span className="font-bold text-violet-400 text-lg">
                  {last ? Math.round(last.confidence * 100) : 0}%
                </span>
              </div>
              <div className="h-2.5 w-full bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-violet-500 rounded-full transition-all" 
                  style={{ width: `${(last?.confidence || 0) * 100}%` }}
                />
              </div>
            </div>
            
            <div className="p-5 bg-violet-500/5 border border-violet-500/20 rounded-xl text-[13px] md:text-sm text-foreground leading-loose text-justify shadow-inner">
              {why.isLoading ? (
                <span className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> در حال استخراج دلایل...
                </span>
              ) : why.data ? (
                <p className="whitespace-pre-line">{why.data.answer}</p>
              ) : (
                <span className="text-muted-foreground">دلیلی ثبت نشده است.</span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* INTERACTIVE PLAYGROUND (Replaces Calculator) */}
        <Card className="h-full flex flex-col border-violet-500/20 shadow-lg shadow-violet-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <LineChart className="h-5 w-5 text-blue-400" /> شبیه‌ساز تحلیل (Playground)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5 flex-1 flex flex-col">
            <p className="text-xs text-muted-foreground">
              می‌خواهید بدانید من در گذشته یا در تایم‌فریم‌های دیگر چه تحلیلی می‌دادم؟ تنظیمات زیر را تغییر دهید.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-foreground mb-2 block">انتخاب تایم‌فریم:</label>
                <div className="flex gap-2">
                  {["15m", "1h", "4h", "1d"].map((tf) => (
                    <Button 
                      key={tf}
                      variant={simTf === tf ? "default" : "outline"} 
                      size="sm"
                      className={`flex-1 ${simTf === tf ? "bg-blue-600 hover:bg-blue-700" : ""}`}
                      onClick={() => setSimTf(tf)}
                    >
                      {tf}
                    </Button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-foreground mb-2 flex items-center gap-1">
                  <Calendar className="h-3 w-3" /> انتخاب بازه زمانی (تاریخ پایان تحلیل):
                </label>
                <select 
                  value={simDate} 
                  onChange={(e) => setSimDate(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="2026-10-01">ابتدای مهر ۱۴۰۵ (آخرین داده‌ها)</option>
                  <option value="2026-07-01">ابتدای تیر ۱۴۰۵ (۳ ماه قبل)</option>
                  <option value="2026-01-01">ابتدای دی ۱۴۰۴ (۹ ماه قبل)</option>
                  <option value="2025-01-01">ابتدای سال ۲۰۲۵ (یک سال قبل)</option>
                </select>
              </div>
            </div>

            <Button 
              className="w-full mt-auto bg-blue-500 hover:bg-blue-600 text-white" 
              onClick={handleSimulate}
              disabled={simulate.isPending}
            >
              {simulate.isPending ? <Loader2 className="h-4 w-4 animate-spin ml-2" /> : <Play className="h-4 w-4 ml-2" />}
              اجرای تحلیل در این تاریخ
            </Button>

            {simResult && (
              <div className="mt-4 space-y-3">
                {simResult.error ? (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
                    {typeof simResult.error === 'string' ? simResult.error : JSON.stringify(simResult.error)}
                  </div>
                ) : simResult.stats ? (
                  <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg text-sm text-blue-200">
                    <p className="font-bold mb-3">آمار شبیه‌سازی در این بازه (۳۰۰ کندل):</p>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-background/50 p-2 rounded">
                        <span className="text-[10px] text-muted-foreground block">تعداد تغییر رژیم:</span>
                        <span className="font-bold text-foreground">{simResult.stats.switches || 0} بار</span>
                      </div>
                      <div className="bg-background/50 p-2 rounded">
                        <span className="text-[10px] text-muted-foreground block">رژیم نهایی:</span>
                        <span className="font-bold text-foreground">{REGIME_FA[simResult.stats.final_regime]?.label || simResult.stats.final_regime || "نامشخص"}</span>
                      </div>
                      <div className="bg-background/50 p-2 rounded">
                        <span className="text-[10px] text-muted-foreground block">ربات‌های فعال در پایان:</span>
                        <span className="font-bold text-foreground">{simResult.stats.final_active_bots?.join("، ") || "نقد (Cash)"}</span>
                      </div>
                      <div className="bg-background/50 p-2 rounded">
                        <span className="text-[10px] text-muted-foreground block">مجموع تحلیل‌ها:</span>
                        <span className="font-bold text-foreground">{simResult.stats.total_ticks || 0} کندل</span>
                      </div>
                    </div>
                    {simResult.decision ? (
                      <div className="bg-background/50 p-3 rounded text-xs leading-relaxed">
                        <div className="flex gap-2 items-center mb-2">
                           <Badge variant="outline" className="bg-blue-500/20 text-blue-300">{simResult.decision.action}</Badge>
                           <span className="text-[10px] text-muted-foreground">اطمینان: {Math.round((simResult.decision.confidence || 0) * 100)}%</span>
                        </div>
                        <p className="font-bold mb-1">دلیل آخرین تصمیم:</p>
                        <p className="text-foreground whitespace-pre-line">{simResult.explanation}</p>
                      </div>
                    ) : (
                      <div className="bg-background/50 p-3 rounded text-xs text-amber-400">
                        در این تاریخ، ربات تصمیم مشخصی نگرفته است.
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
                    داده‌ای برای نمایش وجود ندارد.
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ALTERNATIVES & ACCOUNT */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {last?.alternatives && last.alternatives.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Activity className="h-5 w-5 text-amber-400" /> سناریوهای فرضی
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {last.alternatives.map((alt: any, i: number) => (
                <div key={i} className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-lg bg-secondary/50 border border-border text-sm gap-2">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className={`px-3 py-1 ${REGIME_FA[alt.regime]?.color || ""}`}>
                      روند {REGIME_FA[alt.regime]?.label || alt.regime}
                    </Badge>
                    <span className="text-muted-foreground">
                      {alt.active_bots.length > 0 ? `پیشنهاد: ${alt.active_bots.join("، ")}` : "پیشنهاد: نقد (Cash)"}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Activity className="h-5 w-5 text-amber-400" /> سناریوهای فرضی
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">در حال حاضر سناریوی جایگزینی برای این تحلیل وجود ندارد.</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Wallet className="h-5 w-5" /> وضعیت حساب شما
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">کل سرمایه</p>
              <p className="font-semibold text-lg">{Number(d.capital_total).toLocaleString("fa-IR")} <span className="text-xs font-normal">تومان</span></p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">موجودی نقدی</p>
              <p className="font-semibold text-lg">{Number(d.cash).toLocaleString("fa-IR")} <span className="text-xs font-normal">تومان</span></p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">سود/زیان امروز</p>
              <p className={`font-semibold text-lg ${d.daily_pnl_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {d.daily_pnl_pct}%
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
