"use client";

import Link from "next/link";
import { ClipboardList, Play, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SignalCtaProps {
  symbol: string;
}

export function SignalCta({ symbol }: SignalCtaProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-card p-3">
      <p className="text-xs text-muted-foreground">اقدام بعدی:</p>

      <Link href={`/order-bot?symbol=${symbol}`} className="flex-1 md:flex-none">
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-1.5 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 md:w-auto"
        >
          <ClipboardList className="h-3.5 w-3.5" />
          ثبت سفارش
        </Button>
      </Link>

      <Link
        href={`/paper-trading?symbol=${symbol}`}
        className="flex-1 md:flex-none"
      >
        <Button variant="outline" size="sm" className="w-full gap-1.5 md:w-auto">
          <Play className="h-3.5 w-3.5" />
          Paper Trade
        </Button>
      </Link>

      <Button
        variant="outline"
        size="sm"
        disabled
        title="به زودی"
        className="w-full gap-1.5 opacity-50 md:w-auto"
      >
        <Bell className="h-3.5 w-3.5" />
        هشدار قیمت
      </Button>
    </div>
  );
}
