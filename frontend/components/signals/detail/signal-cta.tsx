"use client";

import Link from "next/link";
import {
  ClipboardList,
  Play,
  Bell,
  Radar,
  BarChart3,
  ArrowUpRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface SignalCtaProps {
  symbol: string;
  /** beginner = نمایش لینک‌های حرفه‌ای (برای signals) | advanced = فقط لینک چارت (برای markets) */
  variant?: "beginner" | "advanced";
}

export function SignalCta({ symbol, variant = "beginner" }: SignalCtaProps) {
  return (
    <div className="space-y-3">
      {/* Row 1 — اقدامات فوری */}
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

      {/* Row 2 — لینک به چارت کامل */}
      <div className="rounded-xl border border-purple-500/20 bg-purple-500/[0.03] p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="flex items-center gap-1.5 text-xs text-purple-300">
            <BarChart3 className="h-3.5 w-3.5" />
            {variant === "advanced"
              ? "چارت اختصاصی با ابزارهای کامل:"
              : "تریدر حرفه‌ای هستی؟ ادامه بده در:"}
          </p>
          <div className="flex gap-2">
            <Link
              href={`/markets/${symbol}/chart`}
              className="flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1.5 text-xs text-purple-300 transition hover:bg-purple-500/20"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              چارت اختصاصی
              <ArrowUpRight className="h-3 w-3" />
            </Link>
            {variant === "beginner" && (
              <Link
                href="/scanner"
                className="flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1.5 text-xs text-purple-300 transition hover:bg-purple-500/20"
              >
                <Radar className="h-3.5 w-3.5" />
                اسکنر بازار
                <ArrowUpRight className="h-3 w-3" />
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
