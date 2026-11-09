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
  Calculator,
  Bitcoin
} from "lucide-react";
import {
  useSarvRouterStatus,
  useSarvRouterWhy,
  useSarvRouterFeedback,
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
  
  // Calculator State
  const [calcAmount, setCalcAmount] = useState<string>("");

  // Set default calculation amount when data loads
  useEffect(() => {
    if (status.data?.last_decision?.risk?.capital_at_risk_tmn) {
      setCalcAmount(status.data.last_decision.risk.capital_at_risk_tmn.toString());
    } else {
      setCalcAmount("10000000"); // Default 10M Toman
    }
  }, [status.data]);

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

  // Calculator Math
  const amount = Number(calcAmount) || 0;
  const feePct = last?.risk?.estimated_cost_pct || 0.55; // default 0.55%
  const estimatedFee = (amount * feePct) / 100;
  const netAmount = amount - estimatedFee;
  const breakevenPct = feePct; // To profit, price must rise by at least feePct

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
              به سروباتس خوش آمدید. من یک ربات معامله‌گر خودکار نیستم که بدون اجازه شما پول را جابه‌جا کنم. 
              من یک <b>دستیار تحلیل‌گر</b> هستم. من میلیون‌ها داده و کندل را در ثانیه بررسی می‌کنم تا روند بازار را تشخیص دهم. 
              سپس با ارائه دلایل شفاف، به شما پیشنهاد می‌دهم که چه کاری انجام دهید. 
              <b> تصمیم نهایی، کلیک روی دکمه تایید، و مدیریت سرمایه کاملاً در اختیار شماست.</b>
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        
        {/* WHY CARD */}
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-violet-400" /> چرا این تصمیم را گرفتم؟
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
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
            
            <div className="p-5 bg-violet-500/5 border border-violet-500/20 rounded-xl text-[13px] md:text-sm text-foreground leading-loose text-justify shadow-inner min-h-[160px]">
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

        {/* INTERACTIVE RISK CALCULATOR CARD */}
        <Card className="h-full border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Calculator className="h-5 w-5 text-rose-400" /> ماشین‌حساب هزینه و ریسک
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium">مبلغی که می‌خواهید وارد کنید (تومان):</label>
              <Input 
                type="number" 
                value={calcAmount} 
                onChange={(e) => setCalcAmount(e.target.value)}
                placeholder="مثلا ۱۰,۰۰۰,۰۰۰"
                className="text-left font-mono text-lg h-12"
                dir="ltr"
              />
            </div>

            <div className="space-y-3 p-4 bg-secondary/30 rounded-xl border border-border">
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">کارمزد صرافی و لغزش قیمت ({feePct}%):</span>
                <span className="font-bold text-rose-400">
                  {Math.round(estimatedFee).toLocaleString("fa-IR")} تومان
                </span>
              </div>
              <div className="flex justify-between items-center text-sm border-t border-border/50 pt-3">
                <span className="text-muted-foreground">سرمایه خالصی که درگیر می‌شود:</span>
                <span className="font-bold text-emerald-400">
                  {Math.round(netAmount).toLocaleString("fa-IR")} تومان
                </span>
              </div>
            </div>

            <p className="text-[11px] text-muted-foreground leading-relaxed text-justify">
              * برای اینکه این معامله شما را وارد سود کند، قیمت باید حداقل <b>{breakevenPct}%</b> رشد کند تا فقط کارمزدها جبران شوند. 
              بازارهای مالی پرریسک هستند، با آگاهی وارد شوید.
            </p>
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
