"use client";

import Link from "next/link";
import { Clock, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { usePortfolio, useWallexStatus } from "@/lib/queries";
import { formatClock } from "@/lib/format";
import { cn } from "@/lib/utils";

export function StatusStrip() {
  const { data: wallex, isLoading: wallexLoading } = useWallexStatus();
  const portfolio = usePortfolio();
  const updated = portfolio.dataUpdatedAt ? formatClock(portfolio.dataUpdatedAt / 1000) : "—";

  const isTradeConnected = wallex?.trade_connected === true;

  const chip = wallexLoading ? null : isTradeConnected ? (
    <Link
      href="/settings/wallex"
      className="inline-flex items-center gap-1.5 rounded-full border border-violet-500/40 bg-violet-500/10 px-3 py-1 text-xs font-semibold text-violet-600 dark:text-violet-400 transition-colors hover:bg-violet-500/20"
    >
      <ShieldCheck className="h-3.5 w-3.5" />
      توکن معاملاتی متصل است
    </Link>
  ) : (
    <Link
      href="/settings/wallex"
      className="inline-flex items-center gap-1.5 rounded-full border border-zinc-500/30 bg-zinc-500/10 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-zinc-500/20"
    >
      <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />
      توکن معاملاتی متصل نیست (برای اتصال کلیک کنید)
    </Link>
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
