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
import { useWallexStatus, useUserPaperV3Status } from "@/lib/queries";
import { formatNumber, formatPct } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const num = (v: unknown): number | null => {
  if (v === null || v === undefined || v === "") return null;
  const x = Number(v);
  return Number.isFinite(x) ? x : null;
};

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
              برای مشاهده، والکس را متصل کنید
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
  const wallex = useWallexStatus();
  const paper = useUserPaperV3Status();

  // ── ۱) دارایی‌های والکس ──
  const balances = wallex.data?.balances ?? [];
  const nonZeroAssets = balances.filter((b) => num(b.total) && num(b.total)! > 0);
  const totalAssets = nonZeroAssets.length;
  const hasWallex = wallex.data?.connected && balances.length > 0;

  // ── ۲) TMN آزاد ──
  const tmnItem = balances.find((b) => b.asset === "TMN");
  const tmn = tmnItem ? num(tmnItem.available) : null;

  // ── ۳) پوزیشن‌های باز Paper ──
  const paperData = paper.data as Record<string, unknown> | undefined;
  const openPositions = (paperData?.open_positions as unknown[]) ?? [];
  const openCount = openPositions.length;
  const paperRunning = paperData?.is_running === true;

  // ── ۴) Paper PnL ──
  const pnlPct = num(paperData?.total_pnl_pct);
  const equity = num(paperData?.equity);
  const pnlTone = pnlPct === null || pnlPct === 0 ? "" : pnlPct > 0 ? "text-emerald-500" : "text-red-500";
  const isPaperIdle = paperData && !paperRunning && (num(paperData.total_trades) ?? 0) === 0 && openCount === 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Kpi
        href="/settings/wallex"
        icon={Wallet}
        tone="emerald"
        label="دارایی‌های والکس"
        loading={wallex.isLoading}
        error={!wallex.isLoading && (!wallex.data?.connected || !!wallex.data?.error)}
        onRetry={() => wallex.refetch()}
        value={hasWallex ? String(totalAssets) : "—"}
        unit={hasWallex ? "دارایی" : undefined}
        valueClass="text-emerald-400"
        sub={hasWallex ? "موجودی‌های واقعی حساب والکس" : "اتصال به والکس برقرار نیست"}
        sub2={hasWallex ? "برای جزئیات کلیک کن" : undefined}
      />
      <Kpi
        href="/settings/wallex"
        icon={Coins}
        tone="amber"
        label="TMN آزاد در والکس"
        loading={wallex.isLoading}
        error={!wallex.isLoading && (!wallex.data?.connected || !!wallex.data?.error)}
        onRetry={() => wallex.refetch()}
        value={tmn === null ? "—" : formatNumber(tmn, { maximumFractionDigits: 0 })}
        unit={tmn !== null ? "TMN" : undefined}
        sub={tmn !== null ? "موجودی واقعی قابل استفاده" : "اتصال به والکس برقرار نیست"}
      />
      <Kpi
        href="/guest"
        icon={ClipboardList}
        tone="blue"
        label="پوزیشن‌های باز (Paper)"
        loading={paper.isLoading}
        error={paper.isError}
        onRetry={() => paper.refetch()}
        value={String(openCount)}
        unit="پوزیشن"
        sub={openCount > 0 ? "در محیط شبیه‌سازی" : "پوزیشن بازی وجود ندارد"}
        sub2={paperRunning ? "Paper در حال اجراست" : undefined}
        sub2Class="text-violet-400"
      />
      <Kpi
        href="/guest"
        icon={FlaskConical}
        tone="violet"
        label="سود/زیان Paper"
        loading={paper.isLoading}
        error={paper.isError}
        onRetry={() => paper.refetch()}
        value={pnlPct === null ? "—" : formatPct(pnlPct)}
        valueClass={pnlTone}
        sub={!paperData ? undefined : paperRunning ? "Paper در حال اجراست" : isPaperIdle ? "Paper اجرا نشده" : "Paper متوقف است"}
        sub2={equity !== null ? `ارزش کل ${formatNumber(equity)}` : undefined}
      />
    </div>
  );
}
