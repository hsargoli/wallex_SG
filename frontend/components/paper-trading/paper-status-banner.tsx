/**
 * Paper Status Banner — نمایش وضعیت running/stopped + شمارنده‌ها.
 * DRY ManualOrderForm — Phase 2.
 */
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type PaperStatusBannerProps = {
  isRunning: boolean;
  openPositionsCount: number;
  tradesCount: number;
  variant?: "guest" | "user";
};

export function PaperStatusBanner({
  isRunning,
  openPositionsCount,
  tradesCount,
  variant = "user",
}: PaperStatusBannerProps) {
  return (
    <Card
      className={cn(
        "border-2",
        isRunning
          ? "border-violet-500/40 bg-violet-500/5"
          : "border-white/10",
      )}
    >
      <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "h-3 w-3 rounded-full",
              isRunning
                ? "animate-pulse bg-emerald-400"
                : "bg-muted-foreground/40",
            )}
          />
          <div>
            <p className="font-semibold">
              {isRunning ? "در حال اجرا" : "متوقف"}
            </p>
            <p className="text-xs text-muted-foreground">
              {isRunning
                ? variant === "guest"
                  ? "Paper هر ۳ دقیقه بازار را چک می‌کند"
                  : "سفارش‌های جدید در Paper ثبت می‌شوند"
                : variant === "guest"
                  ? "برای شروع، دکمه‌ی شروع را بزن"
                  : "برای ثبت سفارش، ابتدا Paper را شروع کن"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">پوزیشن‌های باز</p>
            <p className="font-mono font-bold">{openPositionsCount}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">کل تریدها</p>
            <p className="font-mono font-bold">{tradesCount}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
