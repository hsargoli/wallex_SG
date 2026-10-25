"use client";

import { useMemo } from "react";
import { Sparkles, TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react";
import { useMarkets, useAllSignals } from "@/lib/queries";
import { KeyhanCanvas } from "@/components/keyhan/keyhan-canvas";
import { Card, CardContent } from "@/components/ui/card";

/**
 * Keyhan Market (ADR 0031) — isolated MVP.
 * Fetches top-50 TMN markets by volume, generates signals (from cache),
 * passes to Canvas for progressive reveal. Zero backend changes.
 */
export default function KeyhanPage() {
  const markets = useMarkets();

  const top50 = useMemo(() => {
    if (!markets.data?.items) return [];
    return [...markets.data.items]
      .filter((m) => String(m.symbol).toUpperCase().endsWith("TMN"))
      .sort(
        (a, b) =>
          Number(b.daily_quote_volume || 0) -
          Number(a.daily_quote_volume || 0),
      )
      .slice(0, 50)
      .map((m) => m.symbol);
  }, [markets.data]);

  // Build volume map for star sizing
  const volumeMap = useMemo(() => {
    const map: Record<string, number> = {};
    if (markets.data?.items) {
      for (const m of markets.data.items) {
        map[m.symbol] = Number(m.daily_quote_volume || 0);
      }
    }
    return map;
  }, [markets.data]);

  const signals = useAllSignals(top50, "1h");
  const isLoading = markets.isLoading || signals.isLoading;

  return (
    <div className="flex h-[calc(100vh-3rem)] w-full flex-col gap-3 overflow-hidden">
      {/* Keyhan Canvas */}
      <div className="relative flex-1 overflow-hidden rounded-xl border border-white/10 bg-[#050507]">
        <KeyhanCanvas
          signals={signals.data?.signals ?? []}
          volumeMap={volumeMap}
          isLoading={isLoading}
        />
      </div>

      {/* Info Card */}
      <Card className="shrink-0 border-white/10 bg-white/[0.02] shadow-lg backdrop-blur-md">
        <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-start md:justify-between">
          <div className="max-w-3xl space-y-1.5">
            <h3 className="flex items-center gap-2 text-sm font-bold text-white/90">
              <Sparkles className="h-4 w-4 text-amber-400" />
              درباره کیهان بازار
            </h3>
            <p className="text-xs leading-relaxed text-white/60">
              هر ستاره نماینده یک ارز در بازار است. <strong>اندازه هر ستاره</strong> نشان‌دهنده حجم معاملات ۲۴ ساعته آن ارز است (ارزهای با حجم بالاتر، ستاره‌های بزرگ‌تری دارند) و <strong>رنگ ستاره</strong> بیانگر سیگنال فعلی بازار است. برای مشاهده جزئیات هر ارز، نشانگر ماوس را روی ستاره ببرید یا روی آن کلیک کنید.
            </p>
          </div>

          <div className="flex shrink-0 flex-col gap-2 rounded-lg border border-white/5 bg-black/40 p-3 md:ml-6">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-white/40">راهنمای رنگ‌ها (سیگنال)</span>
            <div className="flex flex-wrap gap-4 text-[11px] text-white/70">
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
                <span>خرید</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                <span>فروش</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-zinc-300" />
                <span>بی‌طرف</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-500" />
                <span>بدون سیگنال (در حال آماده‌سازی)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
