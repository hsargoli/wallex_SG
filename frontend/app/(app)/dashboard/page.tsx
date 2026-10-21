"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useWallexStatus } from "@/lib/queries";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { LiveTickerCard } from "@/components/dashboard/live-ticker-card";
import { PortfolioSignals } from "@/components/dashboard/portfolio-signals";
import { OrdersTimeline } from "@/components/dashboard/orders-timeline";
import { BotsSummary } from "@/components/dashboard/bots-summary";
import { HotMarkets } from "@/components/dashboard/hot-markets";
import { PaperSummary } from "@/components/dashboard/paper-summary";
import { StatusStrip } from "@/components/dashboard/status-strip";
import { BtcChartCard } from "@/components/dashboard/btc-chart-card";
import { SarvAnalysisCard } from "@/components/dashboard/sarv-analysis-card";

export default function DashboardPage() {
  const { data } = useWallexStatus();
  const isConnected = data?.connected ?? false;

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

      {/* اتصال توکن والکس */}
      {!isConnected && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-amber-400" />
              <div>
                <p className="font-semibold text-amber-300">توکن والکس متصل نیست</p>
                <p className="text-xs text-muted-foreground">برای دیدن دارایی‌ها و ثبت سفارش واقعی، توکن خود را متصل کنید.</p>
              </div>
            </div>
            <Button asChild variant="outline" className="border-amber-500/40 text-amber-300 hover:bg-amber-500/10">
              <Link href="/settings/wallex">اتصال توکن</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* ۱) پول من */}
      <KpiCards />

      {/* تیکر زنده بیت‌کوین */}
      <LiveTickerCard symbol="BTCTMN" />

      {/* چارت بیت‌کوین */}
      <BtcChartCard />
      
      {/* کارت تحلیل سرو */}
      <SarvAnalysisCard />

      {/* سیگنال دارایی‌های من */}
      <PortfolioSignals />

      {/* ۳) سفارش‌ها و سیستم */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="space-y-6">
          <OrdersTimeline />
          <HotMarkets />
        </div>
        <div className="space-y-6">
          <PaperSummary />
          <BotsSummary />
        </div>
      </div>
    </div>
  );
}
