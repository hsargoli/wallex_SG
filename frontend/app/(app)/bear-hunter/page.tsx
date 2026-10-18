"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useLiveBotStatus } from "@/lib/hooks/use-bear-hunter";
import { StatusCard } from "@/components/bear-hunter/status-card";
import { SignalCard } from "@/components/bear-hunter/signal-card";
import { ControlsCard } from "@/components/bear-hunter/controls-card";

export default function BearHunterPage() {
  const router = useRouter();
  const { data, isLoading, error } = useLiveBotStatus();

  // Auth guard: 401 -> /login (SPA is public, JWT is the security layer)
  useEffect(() => {
    if (error && (error as any)?.response?.status === 401) {
      router.replace("/login");
    }
  }, [error, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <p className="text-destructive">خطا در دریافت وضعیت ربات. لطفاً وارد شوید.</p>
      </div>
    );
  }

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
