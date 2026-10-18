"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
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
      console.log("[bear-hunter] No token found, redirecting to /login");
      router.replace("/login");
    }
  }, [router]);

  const { data, isLoading, isError, error, refetch } = useLiveBotStatus();

  // Handle 401 globally (token expired)
  useEffect(() => {
    if (isError) {
      const status = (error as any)?.response?.status;
      console.error("[bear-hunter] API Error:", status, error);
      if (status === 401) {
        router.replace("/login");
      }
    }
  }, [isError, error, router]);

  // 1. Mount guard + Loading state
  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // 2. Error state
  if (isError || !data) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-4" dir="rtl">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <h2 className="text-lg font-semibold">خطا در دریافت اطلاعات ربات</h2>
        <p className="text-sm text-muted-foreground">
          {String((error as any)?.response?.data?.detail || (error as any)?.message || "خطای نامشخص")}
        </p>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          تلاش مجدد
        </button>
      </div>
    );
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
