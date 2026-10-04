"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bell,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { usePaginatedSignals } from "@/lib/hooks/use-paginated-signals";
import {
  SignalsFilter,
  type SignalsFilterState,
} from "@/components/signals/signals-filter";
import { SignalRow } from "@/components/signals/signal-row";
import { MarketPagination } from "@/components/markets/market-pagination";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 10;
const LS_TF = "wallex-signals-tf";
const TIMEFRAMES = ["15m", "1h", "4h", "1D"] as const;
type Timeframe = (typeof TIMEFRAMES)[number];

export default function SignalsPage() {
  const markets = useMarkets();
  const [page, setPage] = useState(1);
  const [tf, setTf] = useState<Timeframe>("1h");
  const [filters, setFilters] = useState<SignalsFilterState>({
    search: "",
    quote: "all",
    signal: "all",
    strength: "all",
  });

  // Load saved timeframe
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LS_TF);
      if (saved && TIMEFRAMES.includes(saved as Timeframe)) {
        setTf(saved as Timeframe);
      }
    } catch {
      // ignore
    }
  }, []);

  const handleTfChange = (v: Timeframe) => {
    setTf(v);
    setPage(1);
    try {
      localStorage.setItem(LS_TF, v);
    } catch {
      // ignore
    }
  };

  // Filter markets by quote + search
  const filteredMarkets = useMemo(() => {
    if (!markets.data?.items) return [];
    const search = filters.search.trim().toLowerCase();

    return markets.data.items
      .filter((m) => {
        if (filters.quote !== "all" && m.quote_asset !== filters.quote) {
          return false;
        }
        if (search) {
          const haystack = [
            m.symbol,
            m.base_asset,
            m.fa_name || "",
            m.en_name || "",
          ]
            .join(" ")
            .toLowerCase();
          if (!haystack.includes(search)) return false;
        }
        return true;
      })
      .sort(
        (a, b) =>
          Number(b.daily_quote_volume || 0) -
          Number(a.daily_quote_volume || 0),
      );
  }, [markets.data, filters.search, filters.quote]);

  const allSymbols = useMemo(
    () => filteredMarkets.map((m) => m.symbol),
    [filteredMarkets],
  );

  const filterFn = useCallback(
    (s: { signal: string; strength: string }) => {
      if (filters.signal !== "all" && s.signal !== filters.signal) {
        return false;
      }
      if (filters.strength !== "all" && s.strength !== filters.strength) {
        return false;
      }
      return true;
    },
    [filters.signal, filters.strength],
  );

  
  const needsFilter =
    filters.signal !== "all" || filters.strength !== "all";
  const filterKey = `${filters.signal}-${filters.strength}-${needsFilter ? "all" : page}`;

  // برای جلوگیری از خالی شدن، 2x نماد fetch کن
  const pageStart = (page - 1) * PAGE_SIZE;
  const pageSymbols = allSymbols.slice(
    pageStart,
    pageStart + PAGE_SIZE * 2,
  );

  const { matches, isFetching, isDone, loadedCount, totalCount } =
    usePaginatedSignals({
      symbols: needsFilter ? allSymbols : pageSymbols,
      tf,
      filterFn,
      filterKey,
      pageSize: PAGE_SIZE,
      currentPage: needsFilter ? page : 1,
    });

  // وقتی فیلتر نیست: pagination روی همه‌ی بازارها
  // وقتی فیلتر هست: pagination روی matches
  const totalPages = needsFilter
    ? Math.max(1, Math.ceil(matches.length / PAGE_SIZE))
    : Math.max(1, Math.ceil(filteredMarkets.length / PAGE_SIZE));

  const safePage = Math.min(page, totalPages);

  const paginatedSignals = needsFilter
    ? matches.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)
    : matches.slice(0, PAGE_SIZE);

  const summary = useMemo(
    () => ({
      buy: matches.filter((s) => s.signal === "buy").length,
      sell: matches.filter((s) => s.signal === "sell").length,
      hold: matches.filter((s) => s.signal === "hold").length,
      strong: matches.filter((s) => s.strength === "strong").length,
    }),
    [matches],
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Bell className="h-6 w-6 text-emerald-400" />
            سیگنال‌های معاملاتی
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {markets.isLoading
              ? "در حال بارگذاری..."
              : `${filteredMarkets.length} نماد — مرتب بر اساس حجم`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-0.5 rounded-lg border border-border p-0.5">
            {TIMEFRAMES.map((t) => (
              <Button
                key={t}
                variant="ghost"
                size="sm"
                onClick={() => handleTfChange(t)}
                className={cn(
                  "h-7 px-2.5 font-mono text-xs",
                  tf === t &&
                    "bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/20",
                )}
              >
                {t}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Progress */}
      {isFetching && (
        <Card className="border-emerald-500/20 bg-emerald-500/[0.03]">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex-1">
                <p className="text-xs font-medium">
                  در حال جستجوی سیگنال‌ها...
                </p>
                <p className="mt-0.5 text-[10px] text-muted-foreground">
                  {loadedCount} از {totalCount} نماد بررسی شد — {matches.length}{" "}
                  نتیجه
                </p>
              </div>
              <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all duration-300"
                style={{
                  width: `${totalCount > 0 ? (loadedCount / totalCount) * 100 : 0}%`,
                }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card className="border-emerald-500/20 bg-emerald-500/[0.03]">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <p className="text-[10px] text-muted-foreground">سیگنال خرید</p>
            </div>
            <p className="mt-1 font-mono text-2xl font-bold text-emerald-400">
              {summary.buy}
            </p>
          </CardContent>
        </Card>
        <Card className="border-red-500/20 bg-red-500/[0.03]">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-400" />
              <p className="text-[10px] text-muted-foreground">سیگنال فروش</p>
            </div>
            <p className="mt-1 font-mono text-2xl font-bold text-red-400">
              {summary.sell}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-2">
              <Minus className="h-4 w-4 text-zinc-400" />
              <p className="text-[10px] text-muted-foreground">بی‌طرف</p>
            </div>
            <p className="mt-1 font-mono text-2xl font-bold text-zinc-400">
              {summary.hold}
            </p>
          </CardContent>
        </Card>
        <Card className="border-amber-500/20 bg-amber-500/[0.03]">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-2">
              <span className="text-amber-400">⚡</span>
              <p className="text-[10px] text-muted-foreground">سیگنال قوی</p>
            </div>
            <p className="mt-1 font-mono text-2xl font-bold text-amber-400">
              {summary.strong}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <SignalsFilter
            value={filters}
            onChange={setFilters}
            totalCount={filteredMarkets.length}
            filteredCount={matches.length}
          />
        </CardContent>
      </Card>

      {/* Signals list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              نتایج
              <Badge
                variant="outline"
                className="text-[10px] bg-white/5 border-white/10"
              >
                صفحه {safePage} از {totalPages}
                {!isDone && " (+)"}
              </Badge>
            </span>
            <span className="text-xs font-normal text-muted-foreground">
              تایم‌فریم: {tf}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1.5">
          {/* Headers row */}
          {paginatedSignals.length > 0 && (
            <div className="flex items-center gap-3 px-3 pb-2 text-[10px] font-bold text-muted-foreground border-b border-border/40">
              <div className="h-9 w-9 shrink-0" />
              <div className="min-w-[110px] shrink-0">نماد / قیمت</div>
              <div className="hidden md:block w-[70px] shrink-0 text-center">
                روند
              </div>
              <div className="hidden lg:block w-16 shrink-0 text-center">
                24h
              </div>
              <div className="hidden lg:block w-16 shrink-0 text-center">
                7d
              </div>
              <div className="hidden md:flex min-w-[110px] shrink-0">
                اطمینان
              </div>
              <div className="mr-auto shrink-0">سیگنال</div>
            </div>
          )}

          {markets.isLoading && (
            <>
              {[...Array(PAGE_SIZE)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </>
          )}

          {!markets.isLoading && paginatedSignals.length === 0 && (
            <div className="py-12 text-center">
              <Bell className="mx-auto h-10 w-10 text-muted-foreground/30" />
              <p className="mt-3 text-sm text-muted-foreground">
                {isFetching
                  ? "در حال جستجو..."
                  : "سیگنالی با این فیلترها یافت نشد"}
              </p>
            </div>
          )}

          {!markets.isLoading &&
            paginatedSignals.map((s) => {
              const market = filteredMarkets.find(
                (m) => m.symbol === s.symbol,
              );
              return (
                <SignalRow
                  key={s.symbol}
                  signal={s}
                  quote={market?.quote_asset ?? "TMN"}
                />
              );
            })}
        </CardContent>
      </Card>

      {/* Pagination */}
      <MarketPagination
        page={safePage}
        totalPages={totalPages}
        onPageChange={setPage}
      />
    </div>
  );
}
