"use client";

import { Suspense, useCallback, useMemo } from "react";
import { Zap } from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { usePaginatedScanner } from "@/lib/hooks/use-paginated-scanner";
import {
  useScannerUrlState,
  type ScannerUrlState,
} from "@/lib/hooks/use-scanner-url-state";
import { TimeframeTabs, type Timeframe } from "@/components/scanner/timeframe-tabs";
import { ScannerKPI, type ScannerStats } from "@/components/scanner/scanner-kpi";
import { ScannerFilters } from "@/components/scanner/scanner-filters";
import { ScannerTable } from "@/components/scanner/scanner-table";
import { MarketPagination } from "@/components/markets/market-pagination";
import { Card, CardContent } from "@/components/ui/card";
import type { TrendResult } from "@/lib/api";

const PAGE_SIZE = 15;

function ScannerContent() {
  const { state, update, reset } = useScannerUrlState();
  const markets = useMarkets();

  // ---------- Filter markets by quote + search (global, all 187) ----------
  const filteredMarkets = useMemo(() => {
    if (!markets.data) return [];
    const search = state.search.trim().toLowerCase();
    return markets.data.items
      .filter((m) => {
        // حذف نمادهای بی‌حجم
        if (Number(m.daily_quote_volume || 0) <= 0) return false;
        // quote filter
        const isTMN = m.quote_asset === "TMN";
        if (state.quote === "TMN" && !isTMN) return false;
        if (state.quote === "USDT" && isTMN) return false;
        // search
        if (search) {
          const haystack = [
            m.symbol,
            m.base_asset,
            m.fa_name,
            m.en_name,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
          if (!haystack.includes(search)) return false;
        }
        return true;
      })
      .sort(
        (a, b) =>
          Number(b.daily_quote_volume || 0) - Number(a.daily_quote_volume || 0),
      );
  }, [markets.data, state.search, state.quote]);

  const symbols = useMemo(
    () => filteredMarkets.map((m) => m.symbol),
    [filteredMarkets],
  );

  // ---------- Filter fn for scanned items (signal, strength, RSI, RR) ----------
  const filterFn = useCallback(
    (it: TrendResult) => {
      if (state.signal !== "all" && it.signal !== state.signal) return false;
      if (state.strength !== "all" && it.strength !== state.strength) return false;
      if (state.rsiMin !== null && Number(it.rsi_14 || 0) < state.rsiMin) return false;
      if (state.rsiMax !== null && Number(it.rsi_14 || 0) > state.rsiMax) return false;
      if (state.rrMin !== null && Number(it.risk_reward || 0) < state.rrMin) return false;
      return true;
    },
    [state.signal, state.strength, state.rsiMin, state.rsiMax, state.rrMin],
  );

  const needsFilter =
    state.signal !== "all" ||
    state.strength !== "all" ||
    state.rsiMin !== null ||
    state.rsiMax !== null ||
    state.rrMin !== null;

  const filterKey = `${state.signal}-${state.strength}-${state.rsiMin}-${state.rsiMax}-${state.rrMin}-${needsFilter ? "1" : "0"}`;

  const scan = usePaginatedScanner({
    symbols,
    tf: state.tf,
    filterFn,
    filterKey,
    pageSize: PAGE_SIZE,
    currentPage: state.page,
  });

  // در حال اسکن: بر اساس کل نمادها | اسکن کامل: بر اساس matchها
  const totalPages = scan.isComplete
    ? Math.max(1, Math.ceil(scan.totalMatches / PAGE_SIZE))
    : Math.max(1, Math.ceil(scan.totalSymbols / PAGE_SIZE));

  const stats: ScannerStats = useMemo(() => {
    let bullish = 0, bearish = 0, neutral = 0;
    for (const it of scan.items) {
      if (it.direction === "bullish") bullish++;
      else if (it.direction === "bearish") bearish++;
      else neutral++;
    }
    return { bullish, bearish, neutral, total: scan.items.length };
  }, [scan.items]);

  const handleTf = (tf: Timeframe) => update({ tf, page: 1 });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15">
            <Zap className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">اسکنر بازار</h1>
            <p className="text-xs text-muted-foreground">
              صفحه {state.page} از {totalPages}
              <span className="mx-1.5">—</span>
              <span className="font-mono">
                {scan.totalScanned}/{scan.totalSymbols}
              </span>{" "}
              نماد اسکن‌شده
              {!scan.isComplete && (
                <span className="mr-2 inline-flex items-center gap-1 text-emerald-400">
                  <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                  در حال اسکن
                </span>
              )}
            </p>
          </div>
        </div>

        <TimeframeTabs value={state.tf} onChange={handleTf} />
      </div>

      {/* KPI */}
      <ScannerKPI stats={stats} />

      {/* Filters */}
      <Card className="border-white/5 bg-card">
        <CardContent className="pt-6">
          <ScannerFilters state={state} onUpdate={update} onReset={reset} />
        </CardContent>
      </Card>

      {/* Results header */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          نتایج — تایم‌فریم: <span className="font-mono text-foreground">{state.tf}</span>
        </span>
        <span>
          {scan.items.length} از {scan.totalMatches} نماد منطبق
          {scan.hasMoreToLoad && (
            <span className="ml-2 animate-pulse text-emerald-400">
              ⏳ در حال اسکن...
            </span>
          )}
        </span>
      </div>

      {/* Table */}
      <ScannerTable items={scan.items} loading={scan.isLoading && scan.items.length === 0} />

      {/* Pagination */}
      {totalPages > 1 && (
        <MarketPagination
          page={state.page}
          totalPages={totalPages}
          onPageChange={(p) => update({ page: p })}
        />
      )}
    </div>
  );
}

export default function ScannerPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-sm text-muted-foreground">در حال بارگذاری...</div>
      }
    >
      <ScannerContent />
    </Suspense>
  );
}
