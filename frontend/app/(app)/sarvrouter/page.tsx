"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Activity,
  ShieldAlert,
  ShieldCheck,
  Wallet,
  Bot as BotIcon,
  ArrowRight,
  AlertTriangle,
  Loader2,
  RefreshCw,
} from "lucide-react";
import {
  useSarvRouterStatus,
  useSarvRouterKill,
  useSarvRouterReenable,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatTime, formatPct } from "@/lib/format";

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
  const [confirmKill, setConfirmKill] = useState(false);

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
        <h1 className="text-2xl font-bold">SarvRouter</h1>
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
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="رژیم" value={regime.label} />
          <Stat
            label="ورود جدید"
            value={allowNew ? "مجاز" : "مسدود"}
            tone={allowNew ? "good" : "bad"}
          />
          <Stat
            label="Kill Switch"
            value={isKilled ? "فعال" : "غیرفعال"}
            tone={isKilled ? "bad" : "good"}
          />
          <Stat
            label="آخرین به‌روزرسانی gate"
            value={d.gate?.updated_at ? formatTime(new Date(d.gate.updated_at).getTime() / 1000) : "—"}
          />
        </CardContent>
      </Card>

      {/* Card 2: Active bots + allocations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BotIcon className="h-4 w-4" /> ربات‌های فعال
          </CardTitle>
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
