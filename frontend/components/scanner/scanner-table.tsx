"use client";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScannerTableRow, type ScanItem } from "./scanner-table-row";

interface ScannerTableProps {
  items: ScanItem[];
  loading?: boolean;
}

const COLS = [
  { key: "symbol", label: "نماد / قیمت", hint: "نماد معاملاتی و آخرین قیمت" },
  { key: "change_24h", label: "۲۴h", hint: "درصد تغییر قیمت در ۲۴ ساعت گذشته" },
  { key: "ema_diff", label: "EMA 9/21", hint: "اختلاف درصدی میانگین متحرک ۹ و ۲۱ — مثبت = صعودی" },
  { key: "macd_hist", label: "MACD", hint: "هیستوگرام MACD — مثبت = فشار خرید، منفی = فشار فروش" },
  { key: "rsi_14", label: "RSI", hint: "شاخص قدرت نسبی (۱۴) — زیر ۳۰ اشباع فروش، بالای ۷۰ اشباع خرید" },
  { key: "risk_reward", label: "R/R", hint: "نسبت ریسک به ریوارد — بالاتر بهتر" },
  { key: "atr_pct", label: "ATR%", hint: "نوسان میانگین واقعی (۱۴) به درصد قیمت — بالاتر = پرنوسان‌تر" },
  { key: "bb_pct", label: "BB%", hint: "موقعیت قیمت در باند بولینگر — ۰٪ کف، ۱۰۰٪ سقف" },
  { key: "sparkline", label: "۲۴ کندل", hint: "نمودار قیمت ۲۴ کندل اخیر" },
];

export function ScannerTable({ items, loading }: ScannerTableProps) {
  if (loading) {
    return (
      <div className="space-y-2 rounded-xl border border-white/5 bg-card p-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="rounded-xl border border-white/5 bg-card p-12 text-center text-sm text-muted-foreground">
        نمادی با این فیلترها پیدا نشد
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-white/5 bg-card">
      {/* Header */}
      <div className="grid grid-cols-[minmax(140px,1.4fr)_minmax(70px,0.7fr)_minmax(85px,0.8fr)_minmax(80px,0.8fr)_minmax(65px,0.65fr)_minmax(65px,0.65fr)_minmax(70px,0.7fr)_minmax(70px,0.7fr)_80px] items-center gap-3 border-b border-white/10 bg-white/[0.02] px-4 py-2.5 text-[10px] font-medium text-muted-foreground">
        {COLS.map((c) => (
          <Popover key={c.key}>
            <PopoverTrigger asChild>
              <div className="truncate cursor-help border-b border-dashed border-white/20 pb-0.5 transition hover:text-foreground">
                {c.label}
              </div>
            </PopoverTrigger>
            <PopoverContent
              side="bottom"
              align="start"
              className="w-56 p-2 text-[11px] leading-relaxed text-muted-foreground"
            >
              {c.hint}
            </PopoverContent>
          </Popover>
        ))}
      </div>

      {/* Rows */}
      <div>
        {items.map((item) => (
          <ScannerTableRow key={item.symbol} item={item} />
        ))}
      </div>
    </div>
  );
}
