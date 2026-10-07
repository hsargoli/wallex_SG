"use client";

import Link from "next/link";
import {
  Wallet,
  Coins,
  ClipboardList,
  FlaskConical,
  ArrowUpRight,
  AlertTriangle,
  RotateCw,
} from "lucide-react";
import { useWallet, usePortfolio, useOpenOrders } from "@/lib/queries";
import { formatNumber, formatPct } from "@/lib/format";
import { usePaperLive } from "./use-paper-live";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const num = (v: unknown): number | null => {
  if (v === null || v === undefined || v === "") return null;
  const x = Number(v);
  return Number.isFinite(x) ? x : null;
};

function ago(sec: number): string {
  if (sec < 3600) return `${Math.max(1, Math.floor(sec / 60))} دقیقه پیش`;
  if (sec < 86400) return `${Math.floor(sec / 3600)} ساعت پیش`;
  return `${Math.floor(sec / 86400)} روز پیش`;
}

type Tone = "emerald" | "amber" | "blue" | "violet";
const TONES: Record<Tone, { card: string; icon: string; ico: string }> = {
  emerald: { card: "border-emerald-500/20 from-emerald-500/[0.05] hover:border-emerald-500/40", icon: "bg-emerald-500/15", ico: "text-emerald-400" },
  amber: { card: "border-amber-500/20 from-amber-500/[0.05] hover:border-amber-500/40", icon: "bg-amber-500/15", ico: "text-amber-400" },
  blue: { card: "border-blue-500/20 from-blue-500/[0.05] hover:border-blue-500/40", icon: "bg-blue-500/15", ico: "text-blue-400" },
  violet: { card: "border-violet-500/20 from-violet-500/[0.05] hover:border-violet-500/40", icon: "bg-violet-500/15", ico: "text-violet-400" },
};

function Kpi({
  href, icon: Icon, tone, label, loading, error, onRetry, value, unit, valueClass, sub, sub2, sub2Class,
}: {
  href: string;
  icon: React.ElementType;
  tone: Tone;
  label: string;
  loading?: boolean;
  error?: boolean;
  onRetry?: () => void;
  value: string;
  unit?: string;
  valueClass?: string;
  sub?: string;
  sub2?: string;
  sub2Class?: string;
}) {
  const t = TONES[tone];
  const body = (
    <Card className={cn("h-full overflow-hidden bg-gradient-to-br to-transparent transition-all hover:shadow-lg", t.card)}>
      <CardContent className="pt-5">
        <div className="mb-3 flex items-center justify-between">
          <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", t.icon)}>
            <Icon className={cn("h-4 w-4", t.ico)} />
          </div>
          {error ? (
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
          ) : (
            <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-60 transition-opacity group-hover:opacity-100" />
          )}
        </div>
        <p className="text-[11px] text-muted-foreground">{label}</p>
        {loading ? (
          <Skeleton className="mt-2 h-7 w-32" />
        ) : error ? (
          <>
            <p className="mt-1 text-xl font-bold text-muted-foreground">—</p>
            <button
              type="button"
              onClick={onRetry}
              className="mt-1 inline-flex items-center gap-1 text-[10px] text-amber-500 hover:underline"
            >
              <RotateCw className="h-3 w-3" />
              خطا در دریافت · تلاش دوباره
            </button>
          </>
        ) : (
          <>
            <p className={cn("mt-1 text-xl font-bold", valueClass)}>
              <span dir="ltr" className="inline-block font-mono">{value}</span>
              {unit && <span className="mr-1 text-xs font-normal text-muted-foreground">{unit}</span>}
            </p>
            {sub && <p className="mt-1 text-[10px] text-muted-foreground">{sub}</p>}
            {sub2 && <p className={cn("mt-0.5 text-[10px] text-muted-foreground", sub2Class)}>{sub2}</p>}
          </>
        )}
      </CardContent>
    </Card>
  );
  return error ? <div className="group block">{body}</div> : <Link href={href} className="group block">{body}</Link>;
}

export function KpiCards() {
  const wallet = useWallet();
  const portfolio = usePortfolio();
  const open = useOpenOrders();
  const paper = usePaperLive();

  // ۱) ارزش قابل برداشت سبد (bid)
  const pv = num(portfolio.data?.total_value_tmn_bid);
  const pu = num(portfolio.data?.total_value_usdt_bid);

  // ۲) TMN آزاد
  const tmnItem = wallet.data?.items?.find((b) => b.asset === "TMN");
  const tmn = wallet.data ? (num(tmnItem?.available) ?? 0) : null;

  // ۳) سفارش‌های باز
  const list = (open.data?.orders ?? []) as unknown as Array<Record<string, unknown>>;
  let notional = 0;
  let oldest = 0;
  for (const o of list) {
    const rem = Math.max(0, (num(o.orig_qty) ?? 0) - (num(o.executed_qty) ?? 0));
    notional += (num(o.price) ?? 0) * rem;
    const c = num(o.created_at) ?? 0;
    if (c > 0 && (oldest === 0 || c < oldest)) oldest = c;
  }
  const ageSec = oldest > 0 ? Math.floor(Date.now() / 1000) - oldest : 0;
  const stale = ageSec > 86400;

  // ۴) تست زنده
  const p = paper.data;
  const pnlTone = !p || p.pnlPct === null || p.pnlPct === 0 ? "" : p.pnlPct > 0 ? "text-emerald-500" : "text-red-500";

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Kpi
        href="/portfolio"
        icon={Wallet}
        tone="emerald"
        label="ارزش قابل برداشت سبد"
        loading={portfolio.isLoading}
        error={portfolio.isError || (!portfolio.isLoading && pv === null)}
        onRetry={() => portfolio.refetch()}
        value={pv === null ? "—" : formatNumber(pv, { maximumFractionDigits: 0 })}
        unit="TMN"
        valueClass="text-emerald-400"
        sub={pu !== null ? `≈ ${formatNumber(pu)} USDT · بر پایه‌ی قیمت خرید (bid)` : "بر پایه‌ی قیمت خرید (bid)"}
      />
      <Kpi
        href="/order-bot"
        icon={Coins}
        tone="amber"
        label="TMN آزاد در والکس"
        loading={wallet.isLoading}
        error={wallet.isError || (!wallet.isLoading && tmn === null)}
        onRetry={() => wallet.refetch()}
        value={tmn === null ? "—" : formatNumber(tmn, { maximumFractionDigits: 0 })}
        unit="TMN"
        sub="قابل استفاده برای سفارش جدید"
      />
      <Kpi
        href="/orders"
        icon={ClipboardList}
        tone="blue"
        label="سفارش‌های باز"
        loading={open.isLoading}
        error={open.isError}
        onRetry={() => open.refetch()}
        value={String(list.length)}
        unit="سفارش"
        sub={list.length > 0 ? `ارزش اسمی ≈ ${formatNumber(notional, { maximumFractionDigits: 0 })} TMN` : "سفارش بازی وجود ندارد"}
        sub2={oldest > 0 ? `قدیمی‌ترین: ${ago(ageSec)}${stale ? " — بررسی کن" : ""}` : undefined}
        sub2Class={stale ? "text-amber-500" : undefined}
      />
      <Kpi
        href="/paper-trading"
        icon={FlaskConical}
        tone="violet"
        label="سود/زیان تست زنده"
        loading={paper.isLoading}
        error={paper.isError}
        onRetry={() => paper.refetch()}
        value={!p || p.idle || p.pnlPct === null ? "—" : formatPct(p.pnlPct)}
        valueClass={pnlTone}
        sub={!p ? undefined : p.running ? "تست زنده در حال اجراست" : p.idle ? "تست زنده اجرا نشده" : "تست زنده متوقف است"}
        sub2={p && p.equity !== null && !p.idle ? `ارزش کل ${formatNumber(p.equity)}` : undefined}
      />
    </div>
  );
}
