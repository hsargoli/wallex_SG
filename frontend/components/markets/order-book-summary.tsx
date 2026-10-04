"use client";

import { HelpCircle, TrendingUp, TrendingDown, Info } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber, formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";

interface OrderBookSummaryProps {
  bestBid: string | null | undefined;
  bestAsk: string | null | undefined;
  spread: string | null | undefined;
  spreadPct: string | null | undefined;
  quoteAsset: string;
  loading?: boolean;
}

// ---------- Spread Quality Logic ----------

type SpreadLevel = "tight" | "moderate" | "wide";

function getSpreadLevel(pct: number): SpreadLevel {
  if (pct < 0.1) return "tight";
  if (pct < 0.5) return "moderate";
  return "wide";
}

const SPREAD_STYLES: Record<
  SpreadLevel,
  { color: string; bg: string; label: string; desc: string }
> = {
  tight: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
    label: "باریک",
    desc: "بازار نقدشونده — معامله فوری بدون هزینه‌ی اضافی",
  },
  moderate: {
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
    label: "متوسط",
    desc: "هزینه‌ی معامله متوسط — دقت کن",
  },
  wide: {
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
    label: "پهن",
    desc: "بازار کم‌عمق — هزینه‌ی معامله بالا. با احتیاط معامله کن",
  },
};

// ---------- Tooltip Content ----------

function SpreadTooltip() {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          className="text-muted-foreground/60 transition-colors hover:text-muted-foreground"
          aria-label="توضیح اسپرد"
        >
          <HelpCircle className="h-3 w-3" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-3" align="end">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Info className="h-3.5 w-3.5 text-blue-400" />
            <p className="text-xs font-bold">اسپرد چیست؟</p>
          </div>
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            فاصله‌ی بین <span className="text-emerald-400 font-bold">بهترین قیمت خرید</span>{" "}
            و <span className="text-red-400 font-bold">بهترین قیمت فروش</span>.
            هرچه کمتر باشد، بازار نقدشونده‌تر است و هزینه‌ی معامله پایین‌تر.
          </p>
          <div className="space-y-1.5 rounded-md bg-black/30 p-2">
            <div className="flex items-center gap-2 text-[10px]">
              <div className="h-2 w-2 shrink-0 rounded-full bg-emerald-400" />
              <span className="text-emerald-400">
                باریک{" "}
                <span dir="ltr" className="inline-block font-mono">
                  (&lt;0.1%)
                </span>
              </span>
              <span className="mr-auto text-muted-foreground">عالی</span>
            </div>
            <div className="flex items-center gap-2 text-[10px]">
              <div className="h-2 w-2 shrink-0 rounded-full bg-amber-400" />
              <span className="text-amber-400">
                متوسط{" "}
                <span dir="ltr" className="inline-block font-mono">
                  (0.1-0.5%)
                </span>
              </span>
              <span className="mr-auto text-muted-foreground">قابل قبول</span>
            </div>
            <div className="flex items-center gap-2 text-[10px]">
              <div className="h-2 w-2 shrink-0 rounded-full bg-red-400" />
              <span className="text-red-400">
                پهن{" "}
                <span dir="ltr" className="inline-block font-mono">
                  (&gt;0.5%)
                </span>
              </span>
              <span className="mr-auto text-muted-foreground">خطرناک</span>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// ---------- Main Component ----------

export function OrderBookSummary({
  bestBid,
  bestAsk,
  spread,
  spreadPct,
  quoteAsset,
  loading,
}: OrderBookSummaryProps) {
  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  const spreadPctNum = Number(spreadPct || 0);
  const spreadLevel = getSpreadLevel(spreadPctNum);
  const spreadStyle = SPREAD_STYLES[spreadLevel];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {/* Best Bid */}
      <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/[0.04] to-transparent">
        <CardContent className="pt-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
              <p className="text-[10px] text-muted-foreground">بهترین خرید</p>
            </div>
            <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 font-mono text-[9px] text-emerald-400">
              {quoteAsset}
            </span>
          </div>
          <p className="font-mono text-lg font-bold text-emerald-400">
            {bestBid ? formatPrice(bestBid) : "—"}
          </p>
        </CardContent>
      </Card>

      {/* Best Ask */}
      <Card className="border-red-500/20 bg-gradient-to-br from-red-500/[0.04] to-transparent">
        <CardContent className="pt-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <TrendingDown className="h-3.5 w-3.5 text-red-400" />
              <p className="text-[10px] text-muted-foreground">بهترین فروش</p>
            </div>
            <span className="rounded bg-red-500/15 px-1.5 py-0.5 font-mono text-[9px] text-red-400">
              {quoteAsset}
            </span>
          </div>
          <p className="font-mono text-lg font-bold text-red-400">
            {bestAsk ? formatPrice(bestAsk) : "—"}
          </p>
        </CardContent>
      </Card>

      {/* Spread (absolute) */}
      <Card className={cn("border", spreadStyle.bg)}>
        <CardContent className="pt-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <p className="text-[10px] text-muted-foreground">اسپرد</p>
              <SpreadTooltip />
            </div>
            <span
              className={cn(
                "rounded px-1.5 py-0.5 font-mono text-[9px]",
                spreadLevel === "tight" && "bg-emerald-500/15 text-emerald-400",
                spreadLevel === "moderate" && "bg-amber-500/15 text-amber-400",
                spreadLevel === "wide" && "bg-red-500/15 text-red-400",
              )}
            >
              {quoteAsset}
            </span>
          </div>
          <p className={cn("font-mono text-lg font-bold", spreadStyle.color)}>
            {spread ? formatPrice(spread) : "—"}
          </p>
          <p className="mt-0.5 text-[9px] text-muted-foreground">
            {spreadStyle.label}
          </p>
        </CardContent>
      </Card>

      {/* Spread % */}
      <Card className={cn("border", spreadStyle.bg)}>
        <CardContent className="pt-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <p className="text-[10px] text-muted-foreground">اسپرد ٪</p>
              <SpreadTooltip />
            </div>
            <span
              className={cn(
                "rounded px-1.5 py-0.5 font-mono text-[9px]",
                spreadLevel === "tight" && "bg-emerald-500/15 text-emerald-400",
                spreadLevel === "moderate" && "bg-amber-500/15 text-amber-400",
                spreadLevel === "wide" && "bg-red-500/15 text-red-400",
              )}
            >
              %
            </span>
          </div>
          <p className={cn("font-mono text-lg font-bold", spreadStyle.color)}>
            {spreadPct ? Number(spreadPct).toFixed(4) : "—"}
          </p>
          <p className={cn("mt-0.5 text-[9px]", spreadStyle.color)}>
            {spreadStyle.desc}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
