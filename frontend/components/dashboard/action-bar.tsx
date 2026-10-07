"use client";

import Link from "next/link";
import { Zap, Wallet, ArrowUpRight } from "lucide-react";
import { usePaginatedSignals } from "@/lib/hooks/use-paginated-signals";
import { useMarkets, useBudget } from "@/lib/queries";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function ActionCard({
  href,
  icon: Icon,
  title,
  subtitle,
  tertiary,
  tone,
  loading,
  hint,
}: {
  href: string;
  icon: React.ElementType;
  title: string;
  subtitle: string;
  tertiary?: string;
  tone: "emerald" | "amber" | "blue" | "zinc";
  loading?: boolean;
  hint?: string;
}) {
  const tones = {
    emerald: {
      border: "border-emerald-500/20 hover:border-emerald-500/40",
      bg: "bg-emerald-500/[0.05] hover:bg-emerald-500/[0.08]",
      icon: "bg-emerald-500/15 text-emerald-400",
    },
    amber: {
      border: "border-amber-500/20 hover:border-amber-500/40",
      bg: "bg-amber-500/[0.05] hover:bg-amber-500/[0.08]",
      icon: "bg-amber-500/15 text-amber-400",
    },
    blue: {
      border: "border-blue-500/20 hover:border-blue-500/40",
      bg: "bg-blue-500/[0.05] hover:bg-blue-500/[0.08]",
      icon: "bg-blue-500/15 text-blue-400",
    },
    zinc: {
      border: "border-zinc-500/20 hover:border-zinc-500/40",
      bg: "bg-zinc-500/[0.05] hover:bg-zinc-500/[0.08]",
      icon: "bg-zinc-500/15 text-zinc-400",
    },
  } as const;

  const t = tones[tone];

  if (loading) {
    return <Skeleton className="h-[88px] w-full rounded-xl" />;
  }

  return (
    <Link
      href={href}
      title={hint}
      className="group block"
    >
      <Card
        className={cn(
          "h-full transition-all hover:shadow-lg",
          t.border,
          t.bg,
        )}
      >
        <CardContent className="flex items-center gap-3 p-4">
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
              t.icon,
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold">{title}</p>
            <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
              {subtitle}
            </p>
            {tertiary && (
              <p className="mt-0.5 truncate font-mono text-[10px] text-muted-foreground/70">
                {tertiary}
              </p>
            )}
          </div>
          <ArrowUpRight className="h-4 w-4 shrink-0 text-muted-foreground opacity-60 transition-opacity group-hover:opacity-100" />
        </CardContent>
      </Card>
    </Link>
  );
}

export function ActionBar() {
  const markets = useMarkets();
  const budget = useBudget();

  // استخراج نمادها برای اسکن قوی‌ها
  const symbols = markets.data?.items
    ?.filter((m) => Number(m.daily_quote_volume || 0) > 0)
    .sort(
      (a, b) =>
        Number(b.daily_quote_volume || 0) - Number(a.daily_quote_volume || 0),
    )
    .slice(0, 30)
    .map((m) => m.symbol) ?? [];

  const signals = usePaginatedSignals({
    symbols,
    tf: "1h",
    filterFn: (s) => s.signal === "buy" || s.signal === "sell",
    filterKey: "all-signals",
    pageSize: 50,
    currentPage: 1,
  });

  const budgetUsage = budget.data
    ? Number(budget.data.allocated_budget) > 0
      ? (Number(budget.data.in_use_capital) /
          Number(budget.data.allocated_budget)) *
        100
      : 0
    : 0;

  const buyCount = signals.matches.filter((s) => s.signal === "buy").length;
  const sellCount = signals.matches.filter((s) => s.signal === "sell").length;
  const strongCount = signals.matches.filter(
    (s) => s.strength === "strong",
  ).length;
  const mediumCount = signals.matches.filter(
    (s) => s.strength === "medium",
  ).length;
  const weakCount = signals.matches.filter(
    (s) => s.strength === "weak",
  ).length;
  const totalSignals = signals.matches.length;

  // رنگ بر اساس قوی‌ترین موجود
  const signalTone: "emerald" | "blue" | "zinc" =
    strongCount > 0 ? "emerald" : totalSignals > 0 ? "blue" : "zinc";

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <ActionCard
        href="/signals"
        icon={Zap}
        title={
          signals.isFetching && totalSignals === 0
            ? "در حال بررسی..."
            : `${totalSignals} سیگنال معاملاتی`
        }
        subtitle={`خرید ${buyCount} · فروش ${sellCount}`}
        tertiary={`قوی ${strongCount} · متوسط ${mediumCount} · ضعیف ${weakCount}`}
        tone={signalTone}
        loading={signals.isFetching && totalSignals === 0}
        hint="سیگنال‌های معاملاتی در تایم‌فریم ۱ ساعته. «قوی» یعنی چند اندیکاتور (RSI، EMA، MACD) هم‌جهت تأیید می‌کنن، «متوسط» بعضی تأیید، «ضعیف» تک اندیکاتور."
      />

      <ActionCard
        href="/bot-wallet"
        icon={Wallet}
        title={
          budget.isLoading
            ? "در حال بررسی..."
            : `${budgetUsage.toFixed(0)}٪ بودجه در حال استفاده`
        }
        subtitle={
          budget.data
            ? `آزاد: ${Number(budget.data.available_for_trade || 0).toLocaleString("en-US")} TMN`
            : "—"
        }
        tone="amber"
        loading={budget.isLoading}
        hint="بودجه‌ای که برای ربات‌ها و خودکارسازی ترید در نظر گرفته شده. هر ربات سهم مشخصی از این بودجه رو استفاده می‌کنه. هر وقت خواستی کم یا زیادش کنی، برو به کیف پول ربات."
      />
    </div>
  );
}
