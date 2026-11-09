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
import { formatTime, formatPct } from "@/lib/format";

const ACTION_FA: Record<string, string> = {
  switched: "تغییر روند و ورود جدید",
  pending: "در انتظار تثبیت روند",
  no_change: "بدون تغییر",
  cooldown: "دوره خنک‌سازی (مکث پس از تغییر)",
  kill_switch_active: "توقف اضطراری فعال",
  daily_loss_kill: "توقف به دلیل حد ضرر",
};

const PATH_FA: Record<string, string> = {
  lifecycle: "چرخه عادی ربات",
  kill_switch: "دستور توقف",
  daily_loss: "حد ضرر روزانه",
};

const REGIME_FA: Record<string, { label: string; color: string }> = {
  uptrend: { label: "صعودی", color: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  downtrend: { label: "نزولی", color: "bg-rose-500/15 text-rose-300 border-rose-500/30" },
  range: { label: "رنج", color: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  unknown: { label: "نامشخص", color: "bg-slate-500/15 text-slate-300 border-slate-500/30" },
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
      <div className="container py-8 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (status.isError || !status.data) {
    return (
      <div className="container py-8">
        <Card className="border-rose-500/30">
          <CardHeader>
            <CardTitle className="text-rose-400">خطا در دریافت وضعیت SarvRouter</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              state یا gate در دسترس نیست. لطفاً بعداً تلاش کنید.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => status.refetch()}
            >
              <RefreshCw className="h-4 w-4 ml-2" /> تلاش دوباره
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const d = status.data as unknown as {
    regime: string;
    active_bots: string[];
    allocations: Record<string, number>;
    capital_total: number;
    cash: number;
    daily_pnl_pct: number;
    kill_switch_manual: boolean;
    kill_switch_auto: boolean;
    gate: { allow_new_entries: boolean; updated_at: string; killed_by?: string };
    last_decision?: {
      action: string;
      why: string;
      evidence: Record<string, unknown>;
      confidence: number;
      tick_id: string;
      risk?: {
        fee_pct: number;
        slippage_pct: number;
        spread_pct: number;
        estimated_cost_pct: number;
        capital_at_risk_tmn: number;
        estimated_cost_tmn: number;
        is_hypothetical: boolean;
      } | null;
      alternatives?: Array<{
        regime: string;
        active_bots: string[];
        risk: {
          estimated_cost_pct: number;
          estimated_cost_tmn: number;
          is_hypothetical: boolean;
        };
      }>;
    } | null;
  };

  const regime = REGIME_FA[d.regime] ?? REGIME_FA.unknown;
  const isKilled = d.kill_switch_manual || d.kill_switch_auto;
  const allowNew = d.gate?.allow_new_entries ?? false;

  return (
    <div className="container py-8 space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/bots" className="text-muted-foreground hover:text-foreground">
          <ArrowRight className="h-4 w-4 inline" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">SarvRouter</h1>
          <p className="text-xs text-muted-foreground mt-1">
            دستیار هوشمند تشخیص روند بازار. این سیستم به شما پیشنهاد می‌دهد، اما تصمیم نهایی و تایید معامله همیشه با خود شماست.
          </p>
        </div>
        <Link
          href="/bots/sarv_router"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-violet-400"
        >
          نمای کلی ربات
          <ExternalLink className="h-3 w-3" />
        </Link>
        <Badge variant="outline" className={regime.color}>
          رژیم: {regime.label}
        </Badge>
        {isKilled && (
          <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/30">
            <ShieldAlert className="h-3 w-3 ml-1" /> متوقف
          </Badge>
        )}
      </div>

      {/* Card 1: Regime + Gate */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4" /> وضعیت رژیم و Gate
          </CardTitle>
          <p className="text-[11px] text-muted-foreground">ربات به طور مداوم کندل‌ها را بررسی می‌کند تا بفهمد بازار در حالت صعودی، نزولی یا رنج است.</p>
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="رژیم" value={regime.label} />
          <Stat
            label="ورود جدید"
            value={allowNew ? "مجاز" : "مسدود"}
            tone={allowNew ? "good" : "bad"}
          />
          <Stat
            label="توقف اضطراری"
            value={isKilled ? "فعال" : "غیرفعال"}
            tone={isKilled ? "bad" : "good"}
          />
          <Stat
            label="آخرین به‌روزرسانی وضعیت"
            value={d.gate?.updated_at ? formatTime(new Date(d.gate.updated_at).getTime() / 1000) : "—"}
          />
        </CardContent>
      </Card>

      {/* Card: Last Copilot Decision (phase 1) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4" /> آخرین تصمیم دستیار
          </CardTitle>
          <p className="text-[11px] text-muted-foreground">دلیل پیشنهاد ربات و میزان اطمینان آن در این بخش قابل مشاهده است.</p>
        </CardHeader>
        <CardContent>
          {!d.last_decision ? (
            <p className="text-sm text-muted-foreground">
              هنوز تصمیمی ثبت نشده — منتظر اولین tick.
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium">
                  {d.last_decision.why || d.last_decision.action}
                </p>
                <Badge
                  variant="outline"
                  className={
                    d.last_decision.confidence >= 0.8
                      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                      : d.last_decision.confidence >= 0.5
                      ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                      : "bg-rose-500/15 text-rose-300 border-rose-500/30"
                  }
                >
                  اطمینان: {Math.round(d.last_decision.confidence * 100)}%
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
                <div>
                  <span className="font-medium">اقدام:</span>{" "}
                  {ACTION_FA[d.last_decision.action] || d.last_decision.action}
                </div>
                <div>
                  <span className="font-medium">مسیر:</span>{" "}
                  {PATH_FA[String(d.last_decision.evidence.path)] || "—"}
                </div>
                <div className="col-span-2 flex items-center justify-between">
                  <div>
                    <span className="font-medium">شناسه تصمیم:</span>{" "}
                    <code className="text-[10px]">
                      {d.last_decision.tick_id.slice(0, 8)}
                    </code>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="h-7 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      onClick={() => feedback.mutate({ tick_id: d.last_decision!.tick_id, choice: "accept" })}
                      disabled={feedback.isPending || feedback.isSuccess}
                    >
                      تایید
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="h-7 text-xs bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border-rose-500/30"
                      onClick={() => feedback.mutate({ tick_id: d.last_decision!.tick_id, choice: "reject" })}
                      disabled={feedback.isPending || feedback.isSuccess}
                    >
                      رد
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="h-7 text-xs"
                      onClick={() => {
                        setShowWhy(true);
                        why.refetch();
                      }}
                      disabled={why.isFetching}
                    >
                      <MessageCircleQuestion className="h-3 w-3 ml-1" />
                      چرا؟
                    </Button>
                  </div>
                </div>

                {feedback.isSuccess && (
                  <p className="mt-2 text-xs text-emerald-400">بازخورد شما با موفقیت ثبت شد.</p>
                )}
                {feedback.isError && (
                  <p className="mt-2 text-xs text-rose-400">خطا در ثبت بازخورد.</p>
                )}
                {showWhy && why.data && (
                  <div className="mt-3 p-3 bg-violet-500/10 border border-violet-500/20 rounded-md text-sm text-violet-200">
                    <p className="font-medium mb-1">پاسخ Copilot:</p>
                    <p>{why.data.answer}</p>
                  </div>
                )}
                {showWhy && why.isError && (
                  <p className="mt-2 text-xs text-rose-400">خطا در دریافت پاسخ.</p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Card: Risk Analysis (phase 2) */}
      {d.last_decision?.risk && (
        <Card className={d.last_decision.risk.is_hypothetical ? "border-slate-500/30" : "border-amber-500/40"}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldAlert className="h-4 w-4" /> تحلیل ریسک
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Stat
              label={d.last_decision.risk.is_hypothetical ? "هزینه فرضی (اگر وارد شویم)" : "هزینه پیشنهادی"}
              value={`${Math.round(d.last_decision.risk.estimated_cost_tmn).toLocaleString("fa-IR")} تومان`}
              tone="bad"
            />
            <Stat
              label="درصد هزینه (رفت و برگشت)"
              value={`${d.last_decision.risk.estimated_cost_pct.toFixed(2)}%`}
              tone="bad"
            />
            <Stat
              label="سرمایه درگیر"
              value={`${Math.round(d.last_decision.risk.capital_at_risk_tmn).toLocaleString("fa-IR")} تومان`}
            />
          </CardContent>
        </Card>
      )}

      {/* Card: Alternative Scenarios (phase 5) */}
      {d.last_decision?.alternatives && d.last_decision.alternatives.length > 0 && (
        <Card className="border-slate-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4" /> سناریوهای جایگزین
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-xs text-muted-foreground mb-3">
              اگر روند تغییر کند، Copilot این سناریوها را پیشنهاد می‌دهد:
            </p>
            {d.last_decision.alternatives.map((alt, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded bg-black/[0.03] dark:bg-white/[0.05] text-xs">
                <div>
                  <Badge variant="outline" className="mr-2">
                    {REGIME_FA[alt.regime]?.label ?? alt.regime}
                  </Badge>
                  <span className="text-muted-foreground">
                    {alt.active_bots.length > 0 ? `ربات: ${alt.active_bots.join("، ")}` : "Cash"}
                  </span>
                </div>
                <div className="text-rose-400 font-medium">
                  هزینه: {Math.round(alt.risk.estimated_cost_tmn).toLocaleString("fa-IR")} تومان
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Card 2: Active bots + allocations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BotIcon className="h-4 w-4" /> ربات‌های فعال
          </CardTitle>
          <p className="text-[11px] text-muted-foreground">ربات‌هایی که برای مدیریت سرمایه شما در این روند پیشنهاد شده‌اند.</p>
        </CardHeader>
        <CardContent>
          {d.active_bots.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              هیچ ربات فعالی نیست — Cash
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {d.active_bots.map((slug) => (
                <Link key={slug} href={`/bots/${slug}`}>
                  <Badge variant="outline" className="cursor-pointer hover:bg-accent">
                    {slug} — {formatPct(d.allocations[slug] ?? 0)}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Card 3: Capital */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Wallet className="h-4 w-4" /> سرمایه
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-4">
          <Stat label="کل" value={d.capital_total.toLocaleString("fa-IR")} />
          <Stat label="Cash" value={d.cash.toLocaleString("fa-IR")} />
          <Stat
            label="PnL امروز"
            value={formatPct(d.daily_pnl_pct)}
            tone={d.daily_pnl_pct >= 0 ? "good" : "bad"}
          />
        </CardContent>
      </Card>

      {/* Card 4: Kill switch */}
      <Card className={isKilled ? "border-rose-500/40" : "border-amber-500/30"}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldAlert className="h-4 w-4" /> کنترل اضطراری
          </CardTitle>
          <p className="text-[11px] text-muted-foreground">در صورت نیاز، با این دکمه تمام پیشنهادات ورود جدید را فوراً متوقف کنید.</p>
        </CardHeader>
        <CardContent className="space-y-3">
          {!confirmKill && !isKilled && (
            <Button
              variant="destructive"
              onClick={() => setConfirmKill(true)}
              disabled={kill.isPending}
            >
              <ShieldAlert className="h-4 w-4 ml-2" /> توقف اضطراری
            </Button>
          )}

          {confirmKill && !isKilled && (
            <div className="rounded-md border border-rose-500/30 bg-rose-500/5 p-3 space-y-2">
              <p className="text-sm flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-400 mt-0.5 shrink-0" />
                <span>
                  ورودهای جدید SarvRouter <b>فوراً مسدود</b> می‌شود. ربات‌های در حال اجرا
                  به کار خود ادامه می‌دهند، ولی ورود جدید نخواهند داشت. مطمئنید؟
                </span>
              </p>
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    kill.mutate(undefined, {
                      onSuccess: () => setConfirmKill(false),
                    });
                  }}
                  disabled={kill.isPending}
                >
                  {kill.isPending ? (
                    <><Loader2 className="h-4 w-4 ml-2 animate-spin" /> در حال اجرا</>
                  ) : (
                    <><ShieldAlert className="h-4 w-4 ml-2" /> بله، متوقف کن</>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setConfirmKill(false)}
                  disabled={kill.isPending}
                >
                  لغو
                </Button>
              </div>
            </div>
          )}

          {isKilled && (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3 space-y-2">
              <p className="text-sm flex items-start gap-2">
                <ShieldAlert className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
                <span>
                  SarvRouter متوقف است ({d.kill_switch_manual ? "دستی" : "خودکار"}).
                  ورود جدید مسدود است. برای فعال‌سازی مجدد:
                </span>
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => reenable.mutate()}
                disabled={reenable.isPending}
              >
                {reenable.isPending ? (
                  <><Loader2 className="h-4 w-4 ml-2 animate-spin" /> در حال فعال‌سازی</>
                ) : (
                  <><ShieldCheck className="h-4 w-4 ml-2" /> فعال‌سازی مجدد</>
                )}
              </Button>
            </div>
          )}

          {(kill.isError || reenable.isError) && (
            <p className="text-xs text-rose-400">
              خطا در اعمال تغییر. لطفاً دوباره تلاش کنید.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "good" | "bad";
}) {
  const color =
    tone === "good"
      ? "text-emerald-400"
      : tone === "bad"
      ? "text-rose-400"
      : "text-foreground";
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-sm font-semibold ${color}`}>{value}</p>
    </div>
  );
}
