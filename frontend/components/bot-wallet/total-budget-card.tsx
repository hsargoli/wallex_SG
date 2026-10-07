"use client";

import { Wallet, Lock, Unlock, PieChart } from "lucide-react";
import { useTotalBudget } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function TotalBudgetCard() {
  const total = useTotalBudget();

  if (total.isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  const data = total.data;
  const allocated = Number(data?.total_allocated || 0);
  const inUse = Number(data?.total_in_use || 0);
  const free = Number(data?.unallocated || 0);
  const totalBudget = Number(data?.total_budget || 0);
  const usagePct = totalBudget > 0 ? (inUse / totalBudget) * 100 : 0;
  const allocatedPct = totalBudget > 0 ? (allocated / totalBudget) * 100 : 0;

  const cards = [
    {
      icon: Wallet,
      label: "بودجه کل",
      value: totalBudget,
      sub: "سقف کل سرمایه‌ی ربات‌ها",
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      border: "border-emerald-500/20",
      gradient: "from-emerald-500/[0.05]",
    },
    {
      icon: PieChart,
      label: "تخصیص‌یافته",
      value: allocated,
      sub: `${allocatedPct.toFixed(0)}% از بودجه‌ی کل`,
      color: "text-blue-400",
      bg: "bg-blue-500/15",
      border: "border-blue-500/20",
      gradient: "from-blue-500/[0.05]",
    },
    {
      icon: Lock,
      label: "در گردش",
      value: inUse,
      sub: `${usagePct.toFixed(0)}% در معاملات فعال`,
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      border: "border-amber-500/20",
      gradient: "from-amber-500/[0.05]",
    },
    {
      icon: Unlock,
      label: "آزاد",
      value: free,
      sub: "آماده برای تخصیص",
      color: "text-zinc-400",
      bg: "bg-zinc-500/15",
      border: "border-zinc-500/20",
      gradient: "from-zinc-500/[0.05]",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <Card
            key={i}
            className={cn(
              "overflow-hidden bg-gradient-to-br to-transparent",
              card.border,
              card.gradient,
            )}
          >
            <CardContent className="pt-5">
              <div className="mb-3 flex items-center justify-between">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg",
                    card.bg,
                  )}
                >
                  <Icon className={cn("h-4 w-4", card.color)} />
                </div>
              </div>
              <p className="text-[11px] text-muted-foreground">{card.label}</p>
              <p className={cn("mt-1 font-mono text-xl font-bold", card.color)}>
                {formatNumber(card.value)}{" "}
                <span className="text-xs text-muted-foreground">TMN</span>
              </p>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {card.sub}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
