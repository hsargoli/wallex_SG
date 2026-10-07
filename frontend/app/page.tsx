"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { ActionBar } from "@/components/dashboard/action-bar";
import { OrdersTimeline } from "@/components/dashboard/orders-timeline";
import { BotsSummary } from "@/components/dashboard/bots-summary";
import { HotMarkets } from "@/components/dashboard/hot-markets";
import { PaperSummary } from "@/components/dashboard/paper-summary";
import { StatusStrip } from "@/components/dashboard/status-strip";
import { BtcChartCard } from "@/components/dashboard/btc-chart-card";

export default function DashboardPage() {
  // سلام فقط سمت کلاینت محاسبه می‌شود تا با رندر سرور ناهماهنگ نشود
  const [greeting, setGreeting] = useState("سلام");
  useEffect(() => {
    const hour = new Date().getHours();
    setGreeting(hour < 5 ? "شب بخیر" : hour < 12 ? "صبح بخیر" : hour < 17 ? "وقت بخیر" : "شب بخیر");
  }, []);

  return (
    <div className="space-y-6">
      {/* سربرگ + وضعیت سیستم */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Sparkles className="h-6 w-6 text-amber-400" />
            {greeting} رفیق
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            وضعیت پول، سفارش‌ها و ربات‌ها در یک نگاه
          </p>
        </div>
        <StatusStrip />
      </div>

      {/* ۱) پول من */}
      <KpiCards />

      {/* چارت بیت‌کوین */}
      <BtcChartCard />

      {/* ۲) فرصت‌ها */}
      <ActionBar />

      {/* ۳) سفارش‌ها و سیستم */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <OrdersTimeline />
        <div className="space-y-6">
          <PaperSummary />
          <BotsSummary />
        </div>
      </div>

      {/* ۴) بازار */}
      <HotMarkets />
    </div>
  );
}
