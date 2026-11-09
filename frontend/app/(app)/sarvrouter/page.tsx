"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Activity,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Wallet,
  Loader2,
  RefreshCw,
  Sparkles,
  MessageCircleQuestion,
  TrendingUp,
  TrendingDown,
  Minus,
  HelpCircle,
  CheckCircle2,
  XCircle,
  Info,
  BrainCircuit
} from "lucide-react";
import {
  useSarvRouterStatus,
  useSarvRouterKill,
  useSarvRouterReenable,
  useSarvRouterWhy,
  useSarvRouterFeedback,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

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
  kill_switch_active: "دستیار در حالت تعلیق",
  daily_loss_kill: "توقف به دلیل حد ضرر",
};

export default function SarvRouterPage() {
  const status = useSarvRouterStatus();
  const kill = useSarvRouterKill();
  const reenable = useSarvRouterReenable();
  const why = useSarvRouterWhy();
  const feedback = useSarvRouterFeedback();
  
  const [confirmKill, setConfirmKill] = useState(false);

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
  const isKilled = d.kill_switch_manual || d.kill_switch_auto;

  return (
    <div className="container max-w-5xl py-8 space-y-8">
      
      {/* ONBOARDING SECTION (Always visible) */}
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
            <div className="flex-1 flex items-start gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <b>امنیت سرمایه:</b> من هرگز بدون تایید شما وارد معامله نمی‌شوم. حتی اگر من اشتباه کنم، سرمایه شما تا زمانی که دکمه «تایید و اجرا» را نزنید، در جای امن (نقد) باقی می‌ماند.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* HERO CARD: Dynamic based on Kill Switch */}
      <Card className={`border-2 ${isKilled ? "border-rose-500/50 bg-rose-500/5" : "border-violet-500/30 bg-gradient-to-b from-violet-500/10 to-transparent"}`}>
        <CardContent className="p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
          
          <div className="space-y-4 text-center md:text-right w-full">
            <div className="flex items-center justify-center md:justify-start gap-3">
              <Badge variant="outline" className={`px-3 py-1 text-sm ${regime.color}`}>
                <RegimeIcon className="h-4 w-4 ml-1" />
                وضعیت بازار: {regime.label}
              </Badge>
              {isKilled && (
                <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/30 text-sm">
                  <ShieldAlert className="h-4 w-4 ml-1" /> دستیار تعلیق شده است
                </Badge>
              )}
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-1">تحلیل و پیشنهاد فعلی من:</p>
              <h2 className={`text-2xl font-bold ${isKilled ? "text-rose-400" : "text-foreground"}`}>
                {isKilled ? "توقف تحلیل و پیشنهادات" : (last ? ACTION_FA[last.action] || last.action : "در حال پردازش داده‌ها...")}
              </h2>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-3 w-full md:w-auto shrink-0">
            {isKilled ? (
              <div className="text-center space-y-2">
                <p className="text-xs text-muted-foreground">برای شروع مجدد:</p>
                <Button 
                  className="w-full md:w-56 bg-emerald-500 hover:bg-emerald-600 text-white h-12 text-base"
                  onClick={() => reenable.mutate()}
                  disabled={reenable.isPending}
                >
                  <ShieldCheck className="h-5 w-5 ml-2" /> فعال‌سازی مجدد دستیار
                </Button>
              </div>
            ) : (
              <>
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
              </>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        
        {/* WHY CARD (Detailed & Large) */}
        <Card className={`${isKilled ? "opacity-60" : ""} h-full`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-violet-400" /> چرا این تصمیم را گرفتم؟
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {isKilled ? (
               <p className="text-sm text-muted-foreground">دستیار در حالت توقف است و در حال حاضر تحلیلی انجام نمی‌دهد.</p>
            ) : (
              <>
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
                
                <div className="p-5 bg-violet-500/5 border border-violet-500/20 rounded-xl text-sm text-foreground leading-loose text-justify min-h-[140px] shadow-inner">
                  {why.isLoading ? (
                    <span className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" /> در حال استخراج دلایل از موتور تحلیل...
                    </span>
                  ) : why.data ? (
                    <p className="whitespace-pre-line">{why.data.answer}</p>
                  ) : (
                    <span className="text-muted-foreground">دلیلی ثبت نشده است.</span>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* RISK CARD */}
        <Card className={`${isKilled ? "opacity-60" : ""} h-full`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldAlert className="h-5 w-5 text-rose-400" /> تحلیل هزینه و ریسک
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {isKilled ? (
              <p className="text-sm text-muted-foreground">هزینه‌ای برای این پیشنهاد محاسبه نشده است (سیستم متوقف است).</p>
            ) : last?.risk ? (
              <>
                <div className="flex justify-between items-end border-b border-border/50 pb-3">
                  <span className="text-sm text-muted-foreground">هزینه تخمینی معامله:</span>
                  <div className="text-left">
                    <span className="text-xl font-bold text-rose-400">
                      {Math.round(last.risk.estimated_cost_tmn).toLocaleString("fa-IR")}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">تومان</span>
                  </div>
                </div>
                <div className="flex justify-between items-end border-b border-border/50 pb-3">
                  <span className="text-sm text-muted-foreground">سرمایه درگیر:</span>
                  <div className="text-left">
                    <span className="text-lg font-bold">
                      {Math.round(last.risk.capital_at_risk_tmn).toLocaleString("fa-IR")}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">تومان</span>
                  </div>
                </div>
                <div className="p-3 bg-rose-500/5 rounded-lg border border-rose-500/10">
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    * این یعنی به ازای هر <b>۱ میلیون تومان</b> سرمایه‌گذاری، حدود <b>۵,۵۰۰ تومان</b> بابت کارمزد صرافی و اختلاف قیمت از بین می‌رود. این اعداد به صورت شفاف از تنظیمات صرافی استخراج شده‌اند.
                  </p>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">چون پیشنهاد ورود جدیدی وجود ندارد، هزینه‌ای محاسبه نشده است.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ALTERNATIVES CARD */}
      {!isKilled && last?.alternatives && last.alternatives.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-amber-400" /> سناریوهای فرضی (اگر بازار تغییر کند)
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
                    {alt.active_bots.length > 0 ? `پیشنهاد: ورود به ربات ${alt.active_bots.join("، ")}` : "پیشنهاد: ماندن در حالت نقد (Cash)"}
                  </span>
                </div>
                {alt.risk && (
                  <span className="text-xs font-medium text-rose-400 bg-rose-500/10 px-2 py-1 rounded">
                    هزینه فرضی: {Math.round(alt.risk.estimated_cost_tmn).toLocaleString("fa-IR")} تومان
                  </span>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* FOOTER: CAPITAL & CONTROL */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

        <Card className={isKilled ? "border-rose-500/40 bg-rose-500/5" : ""}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldAlert className="h-5 w-5" /> تعلیق دستیار (اختیاری)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-muted-foreground">
              با زدن این دکمه، دستیار فعلاً از دادن پیشنهاد جدید خودداری می‌کند تا شما با آرامش تصمیم بگیرید.
            </p>
            
            {!confirmKill && !isKilled && (
              <Button variant="outline" className="w-full border-rose-500/30 text-rose-400 hover:bg-rose-500/10" onClick={() => setConfirmKill(true)}>
                تعلیق دستیار
              </Button>
            )}

            {confirmKill && !isKilled && (
              <div className="space-y-2">
                <p className="text-xs text-rose-400">آیا مطمئنید؟</p>
                <div className="flex gap-2">
                  <Button variant="destructive" className="flex-1" onClick={() => { kill.mutate(); setConfirmKill(false); }} disabled={kill.isPending}>
                    بله، تعلیق کن
                  </Button>
                  <Button variant="outline" className="flex-1" onClick={() => setConfirmKill(false)}>لغو</Button>
                </div>
              </div>
            )}

            {isKilled && (
              <Button variant="outline" className="w-full border-emerald-500/50 text-emerald-400 hover:bg-emerald-500/10" onClick={() => reenable.mutate()} disabled={reenable.isPending}>
                <ShieldCheck className="h-4 w-4 ml-2" /> فعال‌سازی مجدد
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
