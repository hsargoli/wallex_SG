"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Activity,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Wallet,
  Bot as BotIcon,
  ArrowRight,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Sparkles,
  MessageCircleQuestion,
  TrendingUp,
  TrendingDown,
  Minus,
  HelpCircle,
  CheckCircle2,
  XCircle
} from "lucide-react";
import {
  useSarvRouterStatus,
  useSarvRouterKill,
  useSarvRouterReenable,
  useSarvRouterWhy,
  useSarvRouterFeedback,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatTime } from "@/lib/format";

const REGIME_FA: Record<string, { label: string; icon: any; color: string }> = {
  uptrend: { label: "صعودی", icon: TrendingUp, color: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  downtrend: { label: "نزولی", icon: TrendingDown, color: "bg-rose-500/15 text-rose-300 border-rose-500/30" },
  range: { label: "رنج (خنثی)", icon: Minus, color: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  unknown: { label: "نامشخص", icon: HelpCircle, color: "bg-slate-500/15 text-slate-300 border-slate-500/30" },
};

const ACTION_FA: Record<string, string> = {
  switched: "تغییر روند و ورود جدید",
  pending: "در انتظار تثبیت روند",
  no_change: "بدون تغییر",
  cooldown: "دوره خنک‌سازی (مکث پس از تغییر)",
  kill_switch_active: "توقف اضطراری فعال",
  daily_loss_kill: "توقف به دلیل حد ضرر",
};

export default function SarvRouterPage() {
  const status = useSarvRouterStatus();
  const kill = useSarvRouterKill();
  const reenable = useSarvRouterReenable();
  const why = useSarvRouterWhy();
  const feedback = useSarvRouterFeedback();
  
  const [confirmKill, setConfirmKill] = useState(false);
  const [showWhy, setShowWhy] = useState(false);

  if (status.isLoading) {
    return (
      <div className="container max-w-4xl py-8 space-y-4">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (status.isError || !status.data) {
    return (
      <div className="container max-w-4xl py-8">
        <Card className="border-rose-500/30 bg-rose-500/5">
          <CardHeader>
            <CardTitle className="text-rose-400">خطا در ارتباط با دستیار</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              اطلاعات وضعیت در دسترس نیست. لطفاً مجدداً تلاش کنید.
            </p>
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
  const allowNew = d.gate?.allow_new_entries ?? false;

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            دستیار SarvRouter
          </h1>
          <p className="text-sm text-muted-foreground mt-2 leading-relaxed max-w-2xl">
            من یک دستیار هوشمند هستم. بازار را تحلیل می‌کنم و به شما پیشنهاد می‌دهم. 
            <b> تصمیم نهایی و تایید معامله همیشه با شماست.</b>
          </p>
        </div>
        <Link href="/bots/sarv_router" className="text-xs text-muted-foreground hover:text-violet-400 flex items-center gap-1 mt-2">
          نمای کلی ربات <ExternalLink className="h-3 w-3" />
        </Link>
      </div>

      {/* HERO CARD: The Main Suggestion */}
      <Card className="border-violet-500/30 bg-gradient-to-b from-violet-500/10 to-transparent">
        <CardContent className="p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-4 text-center md:text-right">
            <div className="flex items-center justify-center md:justify-start gap-3">
              <Badge variant="outline" className={`px-3 py-1 text-sm ${regime.color}`}>
                <RegimeIcon className="h-4 w-4 ml-1" />
                روند بازار: {regime.label}
              </Badge>
              {isKilled && (
                <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/30 text-sm">
                  <ShieldAlert className="h-4 w-4 ml-1" /> متوقف شده
                </Badge>
              )}
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-1">پیشنهاد فعلی من:</p>
              <h2 className="text-2xl font-bold text-foreground">
                {last ? ACTION_FA[last.action] || last.action : "در حال تحلیل..."}
              </h2>
            </div>
          </div>

          {/* Action Buttons (Feedback loop) */}
          <div className="flex flex-col gap-2 w-full md:w-auto">
            <Button 
              className="w-full md:w-40 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 h-12 text-base"
              onClick={() => feedback.mutate({ tick_id: last.tick_id, choice: "accept" })}
              disabled={!last || feedback.isPending || feedback.isSuccess}
            >
              <CheckCircle2 className="h-5 w-5 ml-2" /> موافقم
            </Button>
            <Button 
              className="w-full md:w-40 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/30 h-12 text-base"
              onClick={() => feedback.mutate({ tick_id: last.tick_id, choice: "reject" })}
              disabled={!last || feedback.isPending || feedback.isSuccess}
            >
              <XCircle className="h-5 w-5 ml-2" /> مخالفم
            </Button>
            {feedback.isSuccess && (
              <p className="text-xs text-emerald-400 text-center mt-1">بازخورد شما ثبت شد.</p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* WHY CARD */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-violet-400" /> چرا این پیشنهاد را دادم؟
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">میزان اطمینان من:</span>
              <span className="font-bold text-violet-400">
                {last ? Math.round(last.confidence * 100) : 0}%
              </span>
            </div>
            {/* Confidence Bar */}
            <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-violet-500 rounded-full transition-all" 
                style={{ width: `${(last?.confidence || 0) * 100}%` }}
              />
            </div>
            
            <Button 
              variant="outline" 
              className="w-full mt-2" 
              onClick={() => { setShowWhy(true); why.refetch(); }}
              disabled={why.isFetching}
            >
              {why.isFetching ? <Loader2 className="h-4 w-4 animate-spin ml-2" /> : <MessageCircleQuestion className="h-4 w-4 ml-2" />}
              سوال دیگری دارم
            </Button>

            {showWhy && why.data && (
              <div className="mt-3 p-3 bg-violet-500/10 border border-violet-500/20 rounded-md text-sm text-violet-200">
                <p className="font-medium mb-1">پاسخ دستیار:</p>
                <p className="leading-relaxed">{why.data.answer}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* RISK CARD */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldAlert className="h-5 w-5 text-rose-400" /> تحلیل هزینه و ریسک
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {last?.risk ? (
              <>
                <div className="flex justify-between items-end border-b border-border/50 pb-2">
                  <span className="text-sm text-muted-foreground">هزینه تخمینی معامله:</span>
                  <div className="text-left">
                    <span className="text-lg font-bold text-rose-400">
                      {Math.round(last.risk.estimated_cost_tmn).toLocaleString("fa-IR")}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">تومان</span>
                  </div>
                </div>
                <div className="flex justify-between items-end border-b border-border/50 pb-2">
                  <span className="text-sm text-muted-foreground">سرمایه درگیر:</span>
                  <div className="text-left">
                    <span className="text-sm font-bold">
                      {Math.round(last.risk.capital_at_risk_tmn).toLocaleString("fa-IR")}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">تومان</span>
                  </div>
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed pt-1">
                  * این یعنی به ازای هر <b>۱ میلیون تومان</b> سرمایه‌گذاری، حدود <b>۵,۵۰۰ تومان</b> بابت کارمزد و اختلاف قیمت کسر می‌شود.
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">هزینه‌ای برای این پیشنهاد محاسبه نشده است.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ALTERNATIVES CARD */}
      {last?.alternatives && last.alternatives.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-amber-400" /> اگر بازار تغییر کند چه می‌شود؟
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {last.alternatives.map((alt: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 border border-border text-sm">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={REGIME_FA[alt.regime]?.color || ""}>
                    روند {REGIME_FA[alt.regime]?.label || alt.regime}
                  </Badge>
                  <span className="text-muted-foreground">
                    {alt.active_bots.length > 0 ? `پیشنهاد ورود به ربات ${alt.active_bots.join("، ")}` : "ماندن در حالت نقد (Cash)"}
                  </span>
                </div>
                {alt.risk && (
                  <span className="text-xs font-medium text-rose-400">
                    هزینه: {Math.round(alt.risk.estimated_cost_tmn).toLocaleString("fa-IR")} تومان
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
              <Wallet className="h-5 w-5" /> وضعیت حساب
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
              <ShieldAlert className="h-5 w-5" /> کنترل اضطراری
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-muted-foreground">
              با زدن این دکمه، تمام پیشنهادات ورود جدید فوراً متوقف می‌شوند.
            </p>
            
            {!confirmKill && !isKilled && (
              <Button variant="destructive" className="w-full" onClick={() => setConfirmKill(true)}>
                توقف اضطراری دستیار
              </Button>
            )}

            {confirmKill && !isKilled && (
              <div className="space-y-2">
                <p className="text-xs text-rose-400">آیا مطمئنید؟</p>
                <div className="flex gap-2">
                  <Button variant="destructive" className="flex-1" onClick={() => { kill.mutate(); setConfirmKill(false); }} disabled={kill.isPending}>
                    بله، متوقف کن
                  </Button>
                  <Button variant="outline" className="flex-1" onClick={() => setConfirmKill(false)}>لغو</Button>
                </div>
              </div>
            )}

            {isKilled && (
              <Button variant="outline" className="w-full border-emerald-500/50 text-emerald-400 hover:bg-emerald-500/10" onClick={() => reenable.mutate()} disabled={reenable.isPending}>
                <ShieldCheck className="h-4 w-4 ml-2" /> فعال‌سازی مجدد دستیار
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
