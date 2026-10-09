"use client";

import Link from "next/link";
import { ArrowUpRight, LineChart } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SignalsChart } from "@/components/signals/signals-chart";
import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/info-tip";

interface ChartPreviewProps {
  symbol: string;
  indicators: unknown;
  levels: unknown;
  height?: number;
  title?: string;
  href?: string;
  visibleCandles?: number;
  /** timeframes tabs داخل کارت */
  timeframes?: readonly string[];
  currentTimeframe?: string;
  onTimeframeChange?: (tf: string) => void;
}

export function ChartPreview({
  symbol,
  indicators,
  levels,
  height = 220,
  title = "نمودار سریع",
  href,
  visibleCandles = 60,
  timeframes,
  currentTimeframe,
  onTimeframeChange,
}: ChartPreviewProps) {
  const chartHref = href ?? `/markets/${symbol}/chart`;
  const showTf = timeframes && timeframes.length > 0 && onTimeframeChange;

  return (
    <Card className="border-white/5 bg-[#0f0f17]">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0 border-b border-white/5 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <LineChart className="h-4 w-4 text-emerald-400" />
          {title}
          <InfoTip text="نمودار کندل‌استیک با EMA (میانگین متحرک)، باند بولینگر و سطوح کلیدی (Pivot و S/R). برای دیدن کامل، روی «چارت کامل» کلیک کن." />
        </CardTitle>

        <div className="flex items-center gap-2">
          {showTf && (
            <div className="flex items-center gap-0.5 rounded-lg border border-white/10 bg-background/60 p-0.5">
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => onTimeframeChange(tf)}
                  className={cn(
                    "rounded-md px-2 py-0.5 font-mono text-[11px] transition-colors",
                    currentTimeframe === tf
                      ? "bg-emerald-500/15 text-emerald-400"
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>
          )}

          <Link href={chartHref}>
            <Button
              size="sm"
              className="gap-1.5 bg-emerald-600 text-white hover:bg-emerald-500"
            >
              چارت کامل
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        <SignalsChart
          indicators={indicators as never}
          levels={levels as never}
          height={height}
          visibleCandles={visibleCandles}
          bare
        />
      </CardContent>
    </Card>
  );
}
