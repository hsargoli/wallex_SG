"use client";

import { Sparkles, TrendingUp } from "lucide-react";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { ActionBar } from "@/components/dashboard/action-bar";
import { OrdersTimeline } from "@/components/dashboard/orders-timeline";
import { BotsSummary } from "@/components/dashboard/bots-summary";
import { HotMarkets } from "@/components/dashboard/hot-markets";

export default function DashboardPage() {
  // Greeting based on time of day
  const hour = new Date().getHours();
  const greeting =
    hour < 5
      ? "شب بخیر"
      : hour < 12
        ? "صبح بخیر"
        : hour < 17
          ? "وقت بخیر"
          : "شب بخیر";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Sparkles className="h-6 w-6 text-amber-400" />
            {greeting} رفیق
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            نگاهی به وضعیت بازار و ربات‌های معاملاتی
          </p>
        </div>
      </div>

      {/* Action Bar — کارهای فوری */}
      <ActionBar />

      {/* KPI Cards */}
      <KpiCards />

      {/* Timeline + Bots */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <OrdersTimeline />
        <BotsSummary />
      </div>

      {/* Hot Markets */}
      <HotMarkets />
    </div>
  );
}
