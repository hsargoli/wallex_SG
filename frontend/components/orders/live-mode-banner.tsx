"use client";

import { useQuery } from "@tanstack/react-query";
import { ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { getTradingMode } from "@/lib/api";

export function LiveModeBanner() {
  const q = useQuery({
    queryKey: ["trading-mode"],
    queryFn: getTradingMode,
    refetchInterval: 30_000,
    retry: 1,
  });

  if (q.isLoading) return null;

  if (q.isError || !q.data) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
        <ShieldQuestion className="h-5 w-5 shrink-0" />
        وضعیت معامله‌ی واقعی نامشخص است (پاسخی از سرور نیامد). تا روشن‌شدن وضعیت، سفارش نفرست.
      </div>
    );
  }

  if (q.data.live_enabled) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">
        <ShieldAlert className="h-5 w-5 shrink-0" />
        <div>
          <b>معامله‌ی واقعی فعال است.</b> هر سفارش با پول واقعی روی والکس ثبت می‌شود.
          برای آزمایش، مقدار حداقلی و قیمتی خیلی دور از بازار بگذار و فوراً لغو کن.
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-xl border border-zinc-500/30 bg-zinc-500/10 p-3 text-sm text-muted-foreground">
      <ShieldCheck className="h-5 w-5 shrink-0 text-emerald-500" />
      <div>
        <b>معامله‌ی واقعی غیرفعال است.</b> سفارش‌ها به والکس ارسال نمی‌شوند.
        برای فعال‌سازی، پرچم <span className="font-mono" dir="ltr">{q.data.field.toUpperCase()}</span> را در تنظیمات بک‌اند روشن کن.
      </div>
    </div>
  );
}
