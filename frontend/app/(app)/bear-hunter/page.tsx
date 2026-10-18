"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { getUserToken } from "@/lib/auth";
import { useLiveBotStatus } from "@/lib/hooks/use-bear-hunter";
import { StatusCard } from "@/components/bear-hunter/status-card";
import { SignalCard } from "@/components/bear-hunter/signal-card";
import { ControlsCard } from "@/components/bear-hunter/controls-card";

export default function BearHunterPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!getUserToken()) {
      router.replace("/login");
    }
  }, [router]);

  const { data, isLoading } = useLiveBotStatus();

  // 1. Mount guard + Loading state
  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // 2. If no data (e.g., redirecting), render nothing to avoid flicker
  if (!data) {
    return null;
  }

  // 3. Safe to render
  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-6" dir="rtl">
      <div>
        <h1 className="text-3xl font-bold mb-1">🐻 Bear Hunter</h1>
        <p className="text-muted-foreground text-sm">
          ربات Short برای بازار نزولی والکس — {data.capital_tmn.toLocaleString("fa-IR")} تومان
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatusCard data={data} />
        <SignalCard />
      </div>

      <ControlsCard isKilled={data.is_killed} idle={data.idle} />

      {data.waiting_liquidity_since && (
        <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-sm">
          ⚠️ ربات آماده است ولی والکس نقدینگی وام‌دهی ندارد. از{" "}
          {new Date(data.waiting_liquidity_since).toLocaleString("fa-IR")} منتظر است.
        </div>
      )}
    </div>
  );
}
