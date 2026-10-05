"use client";

import Link from "next/link";
import {
  ClipboardList,
  Play,
  Bell,
  Radar,
  BarChart3,
  BookOpen,
  ArrowUpRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SignalCtaProps {
  symbol: string;
}

export function SignalCta({ symbol }: SignalCtaProps) {
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

      {/* Row 2 — ادامه برای حرفه‌ای‌ها */}
      <div className="rounded-xl border border-purple-500/20 bg-purple-500/[0.03] p-3">
        <p className="mb-2 flex items-center gap-1.5 text-xs text-purple-300">
          <BookOpen className="h-3.5 w-3.5" />
          تریدر حرفه‌ای هستی؟ ادامه بده در:
        </p>
        <div className="grid gap-2 md:grid-cols-3">
          <AdvancedLink
            href={`/markets/${symbol}/chart`}
            icon={BarChart3}
            title="چارت پیشرفته"
            subtitle="EMA · Bollinger · RSI · MACD · سطوح"
          />
          <AdvancedLink
            href="/scanner"
            icon={Radar}
            title="اسکنر بازار"
            subtitle="فیلتر چند تایم‌فریم · مقایسه نمادها"
          />
          <AdvancedLink
            href={`/markets/${symbol}`}
            icon={BookOpen}
            title="تحلیل کامل نماد"
            subtitle="دفتر سفارش · سطوح کلیدی · Confluence"
          />
        </div>
      </div>
    </div>
  );
}

function AdvancedLink({
  href,
  icon: Icon,
  title,
  subtitle,
}: {
  href: string;
  icon: React.ElementType;
  title: string;
  subtitle: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center gap-3 rounded-lg border border-white/5 bg-background/40 p-3 transition-all",
        "hover:border-purple-500/30 hover:bg-purple-500/[0.05]",
      )}
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-purple-500/15 text-purple-400">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-bold">{title}</p>
        <p className="mt-0.5 truncate text-[10px] text-muted-foreground">
          {subtitle}
        </p>
      </div>
      <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
    </Link>
  );
}
