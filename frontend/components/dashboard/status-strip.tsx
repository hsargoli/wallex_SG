"use client";

import Link from "next/link";
import { Clock, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { usePortfolio } from "@/lib/queries";
import { useLiveMode } from "@/lib/hooks/use-live-mode";
import { formatClock } from "@/lib/format";
import { cn } from "@/lib/utils";

export function StatusStrip() {
  const { liveOn, known, loading } = useLiveMode();
  const portfolio = usePortfolio();
  const updated = portfolio.dataUpdatedAt ? formatClock(portfolio.dataUpdatedAt / 1000) : "—";

  const chip = loading ? null : !known ? (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-600 dark:text-amber-400">
      <ShieldQuestion className="h-3.5 w-3.5" />
      وضعیت معامله‌ی واقعی نامشخص
    </span>
  ) : liveOn ? (
    <Link
      href="/order-bot"
      className="inline-flex items-center gap-1.5 rounded-full border border-red-500/40 bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-600 dark:text-red-400"
    >
      <ShieldAlert className="h-3.5 w-3.5" />
      معامله‌ی واقعی فعال
    </Link>
  ) : (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border border-zinc-500/30 bg-zinc-500/10 px-3 py-1 text-xs text-muted-foreground")}>
      <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
      معامله‌ی واقعی غیرفعال
    </span>
  );

  return (
    <div className="flex flex-wrap items-center gap-3">
      {chip}
      <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
        <Clock className="h-3 w-3" />
        به‌روزرسانی <span dir="ltr" className="font-mono">{updated}</span>
      </span>
    </div>
  );
}
