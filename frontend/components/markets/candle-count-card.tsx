"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CandleCount, CandleCountItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { InfoTip } from "@/components/ui/info-tip";

interface Props {
  data: CandleCount | null;
}

type CandleKey = "h1" | "h24" | "d7" | "d30" | "y1";

const PERIODS: Array<{ key: CandleKey; label: string }> = [
  { key: "h1", label: "۴ ساعت اخیر" },
  { key: "h24", label: "۲۴ ساعت" },
  { key: "d7", label: "۷ روز" },
  { key: "d30", label: "۳۰ روز" },
  { key: "y1", label: "۱ سال" },
];

function Row({ label, item }: { label: string; item: CandleCountItem | null }) {
  if (!item) {
    return (
      <div className="flex items-center justify-between border-b border-border/30 py-2 text-xs last:border-0">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-muted-foreground">—</span>
      </div>
    );
  }

  const greenPct = item.green_pct;
  const isBuyer = greenPct >= 55;
  const isSeller = greenPct <= 45;

  return (
    <div className="border-b border-border/30 py-2.5 last:border-0">
      <div className="mb-1.5 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span
          className={cn(
            "font-mono font-bold",
            isBuyer
              ? "text-emerald-400"
              : isSeller
                ? "text-red-400"
                : "text-zinc-400",
          )}
        >
          {greenPct.toFixed(0)}٪ صعودی
        </span>
      </div>

      {/* نوار */}
      <div className="flex h-1.5 overflow-hidden rounded-full bg-red-500/30">
        <div
          className="bg-emerald-500 transition-all"
          style={{ width: `${greenPct}%` }}
        />
      </div>

      <div className="mt-1.5 flex items-center justify-between text-[10px] text-muted-foreground">
        <span>
          <span className="text-emerald-400">■</span> {item.green} سبز
        </span>
        <span className="font-mono">{item.total} کندل</span>
        <span>
          {item.red} قرمز <span className="text-red-400">■</span>
        </span>
      </div>
    </div>
  );
}

export function CandleCountCard({ data }: Props) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <BarChart3 className="h-4 w-4 text-blue-400" />
          کندل‌های سبز و قرمز
          <InfoTip text="درصد کندل‌های صعودی (سبز، close>open) به کل کندل‌ها. بالای ۵۵٪ = فشار خرید، زیر ۴۵٪ = فشار فروش." />
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {PERIODS.map(({ key, label }) => (
          <Row key={key} label={label} item={data?.[key] ?? null} />
        ))}
      </CardContent>
    </Card>
  );
}
