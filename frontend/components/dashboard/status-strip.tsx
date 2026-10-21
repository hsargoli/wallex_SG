"use client";

import Link from "next/link";
import { Clock, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { useWallexStatus } from "@/lib/queries";
import { formatClock } from "@/lib/format";
import { cn } from "@/lib/utils";

export function StatusStrip() {
  const { data: wallex, isLoading: wallexLoading, dataUpdatedAt } = useWallexStatus();
  const updated = dataUpdatedAt ? formatClock(dataUpdatedAt / 1000) : "—";

  const isTradeConnected = wallex?.trade_connected === true;
  const isViewConnected = wallex?.view_connected === true;

  let chip = null;

  if (wallexLoading) {
    chip = null;
  } else if (isTradeConnected && isViewConnected) {
    chip = (
      <Link
        href="/settings/wallex"
        className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 transition-colors hover:bg-emerald-500/20"
      >
        <ShieldCheck className="h-3.5 w-3.5" />
        هر دو توکن (دیدن و معاملات) متصل هستند
      </Link>
    );
  } else if (isViewConnected) {
    chip = (
      <Link
        href="/settings/wallex"
        className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 transition-colors hover:bg-amber-500/20"
      >
        <ShieldAlert className="h-3.5 w-3.5" />
        توکن دیدبانی متصل است (برای ترید، توکن معاملاتی را وصل کنید)
      </Link>
    );
  } else if (isTradeConnected) {
    chip = (
      <Link
        href="/settings/wallex"
        className="inline-flex items-center gap-1.5 rounded-full border border-violet-500/40 bg-violet-500/10 px-3 py-1 text-xs font-semibold text-violet-600 dark:text-violet-400 transition-colors hover:bg-violet-500/20"
      >
        <ShieldCheck className="h-3.5 w-3.5" />
        توکن معاملاتی متصل است (بدون دیدبانی)
      </Link>
    );
  } else {
    chip = (
      <Link
        href="/settings/wallex"
        className="inline-flex items-center gap-1.5 rounded-full border border-zinc-500/30 bg-zinc-500/10 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-zinc-500/20"
      >
        <ShieldAlert className="h-3.5 w-3.5 text-zinc-500" />
        هیچ توکنی متصل نیست (برای اتصال کلیک کنید)
      </Link>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      {chip}
            <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground/80" title="داده‌ها به صورت خودکار هر ۳۰ ثانیه دریافت می‌شوند">
        <Clock className="h-3 w-3" />
        آخرین دریافت داده: <span dir="ltr" className="font-mono">{updated}</span>
      </span>
    </div>
  );
}
