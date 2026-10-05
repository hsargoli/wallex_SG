"use client";

import Link from "next/link";
import { Zap, Wallet, ClipboardList, ArrowUpRight } from "lucide-react";
import { usePaginatedSignals } from "@/lib/hooks/use-paginated-signals";
import { useMarkets, useOpenOrders, useBudget } from "@/lib/queries";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function ActionCard({
  href,
  icon: Icon,
  title,
  subtitle,
  tone,
  loading,
}: {
  href: string;
  icon: React.ElementType;
  title: string;
  subtitle: string;
  tone: "emerald" | "amber" | "blue";
  loading?: boolean;
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
  } as const;

  const t = tones[tone];

  if (loading) {
    return <Skeleton className="h-[88px] w-full rounded-xl" />;
  }

  return (
    <Link href={href} className="group block">
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
          </div>
          <ArrowUpRight className="h-4 w-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
        </CardContent>
      </Card>
    </Link>
  );
}

export function ActionBar() {
  const markets = useMarkets();
  const orders = useOpenOrders();
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
    filterFn: (s) => s.signal === "buy" && s.strength === "strong",
    filterKey: "strong-buy",
    pageSize: 5,
    currentPage: 1,
  });

  const openOrdersCount = orders.data?.orders?.length ?? 0;
  const budgetUsage = budget.data
    ? Number(budget.data.allocated_budget) > 0
      ? (Number(budget.data.in_use_capital) /
          Number(budget.data.allocated_budget)) *
        100
      : 0
    : 0;

  const strongBuyCount = signals.matches.length;

  return (
    <div className="grid gap-3 md:grid-cols-3">
      <ActionCard
        href="/signals?signal=buy&strength=strong"
        icon={Zap}
        title={
          signals.isFetching && strongBuyCount === 0
            ? "در حال بررسی..."
            : strongBuyCount > 0
              ? `${strongBuyCount} سیگنال خرید قوی`
              : "سیگنال قوی نداری"
        }
        subtitle={
          strongBuyCount > 0
            ? "برو ببین کدوم نمادها"
            : "بازار آرومه — صبر کن"
        }
        tone="emerald"
        loading={signals.isFetching && strongBuyCount === 0}
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
            ? `آزاد: ${Number(budget.data.available_for_trade || 0).toLocaleString("fa-IR")} TMN`
            : "—"
        }
        tone="amber"
        loading={budget.isLoading}
      />

      <ActionCard
        href="/orders"
        icon={ClipboardList}
        title={
          orders.isLoading
            ? "در حال بررسی..."
            : openOrdersCount > 0
              ? `${openOrdersCount} سفارش باز`
              : "سفارش بازی نداری"
        }
        subtitle={
          openOrdersCount > 0 ? "وضعیت سفارش‌ها رو ببین" : "همه‌چیز مرتبه"
        }
        tone="blue"
        loading={orders.isLoading}
      />
    </div>
  );
}
