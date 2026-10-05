"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bell,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Info,
  Filter,
  X,
} from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { useBatchSignals } from "@/lib/queries";
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
        // فقط بازارهایی که داده‌ی معتبر دارن
        if (!m.last_price || Number(m.last_price) <= 0) return false;
        if (Number(m.daily_quote_volume || 0) <= 0) return false;

        // فیلتر quote
        if (filters.quote !== "all" && m.quote_asset !== filters.quote) {
          return false;
        }

        // فیلتر جستجو
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

  // ---------- تصمیم: چه چیزی fetch کنیم ----------
  // بدون فیلتر: فقط 10 نماد صفحه‌ی فعلی (سریع)
  // با فیلتر: همه‌ی 373 نماد (چون ممکنه نتیجه خارج از صفحه باشه)
  const pageStart = (page - 1) * PAGE_SIZE;
  const symbolsToFetch = needsFilter
    ? allSymbols
    : allSymbols.slice(pageStart, pageStart + PAGE_SIZE);

  const batchQuery = useBatchSignals(symbolsToFetch, tf);
  const matches = batchQuery.data?.signals ?? [];

  // ---------- فیلتر سمت کلاینت ----------
  const filteredMatches = needsFilter
    ? matches.filter(filterFn)
    : matches;

  // ---------- Pagination ----------
  // بدون فیلتر: از کل بازارها (373)
  // با فیلتر: از نتایج فیلترشده
  const totalPages = needsFilter
    ? Math.max(1, Math.ceil(filteredMatches.length / PAGE_SIZE))
    : Math.max(1, Math.ceil(filteredMarkets.length / PAGE_SIZE));

  const safePage = Math.min(page, totalPages);

  // ---------- نمایش ----------
  const paginatedSignals = needsFilter
    ? filteredMatches.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)
    : matches;

  // ---------- وضعیت ----------
  const isFetching = batchQuery.isFetching;
  const isDone = !needsFilter || !isFetching;
  const loadedCount = symbolsToFetch.length;
  const totalCount = needsFilter ? allSymbols.length : symbolsToFetch.length;
  const isEmptyPage = paginatedSignals.length === 0 && isFetching;

  const summary = useMemo(() => {
    const buy = matches.filter((s) => s.signal === "buy");
    const sell = matches.filter((s) => s.signal === "sell");
    return {
      buy: buy.length,
      sell: sell.length,
      hold: matches.filter((s) => s.signal === "hold").length,
      strong: matches.filter((s) => s.strength === "strong").length,
      buyBreakdown: {
        strong: buy.filter((s) => s.strength === "strong").length,
        medium: buy.filter((s) => s.strength === "medium").length,
        weak: buy.filter((s) => s.strength === "weak").length,
      },
      sellBreakdown: {
        strong: sell.filter((s) => s.strength === "strong").length,
        medium: sell.filter((s) => s.strength === "medium").length,
        weak: sell.filter((s) => s.strength === "weak").length,
      },
    };
  }, [matches]);

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

      {/* راهنمای شفاف برای کاربر جدید */}
      <Card className="border-blue-500/20 bg-blue-500/[0.03]">
        <CardContent className="flex items-start gap-3 py-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/15">
            <Info className="h-4 w-4 text-blue-400" />
          </div>
          <div className="flex-1 space-y-1">
            <p className="text-xs font-medium text-blue-300">
              آمار زیر فقط برای همین صفحه و همین تایم‌فریم (
              <span className="font-mono font-bold">{tf}</span>) است
            </p>
            <p className="text-[11px] leading-relaxed text-muted-foreground">
              سیگنال‌ها بر اساس تایم‌فریم تغییر می‌کنن — یه نماد ممکنه در ۱۵ دقیقه
              «خرید» باشه ولی در ۴ ساعت «فروش». برای دیدن تصویر کامل، تایم‌فریم‌های
              مختلف رو ببین. اعداد پایین با هر تغییر به‌روز می‌شن.
            </p>
          </div>
        </CardContent>
      </Card>

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
                  width: '100%',
                }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI — Action-Oriented */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiAction
          label="سیگنال خرید"
          count={summary.buy}
          breakdown={summary.buyBreakdown}
          tone="emerald"
          icon={TrendingUp}
          hint="تعداد نمادهایی که در این تایم‌فریم سیگنال «خرید» دارن. تفکیک: قوی (چند اندیکاتور هم‌جهت)، متوسط (بعضی تأیید)، ضعیف (تک اندیکاتور)."
        />
        <KpiAction
          label="سیگنال فروش"
          count={summary.sell}
          breakdown={summary.sellBreakdown}
          tone="red"
          icon={TrendingDown}
          hint="تعداد نمادهایی که در این تایم‌فریم سیگنال «فروش» دارن. یعنی اندیکاتورها احتمال کاهش قیمت رو می‌دن."
        />
        <KpiAction
          label="فرصت‌های قوی"
          count={summary.strong}
          tone="amber"
          icon={Zap}
          hint="سیگنال‌های «قوی» شامل خرید و فروش. یعنی چند اندیکاتور مستقل (RSI، EMA، MACD) هم‌جهت تأیید می‌کنن — فرصت‌های با اطمینان بالاتر."
        />
        <KpiAction
          label="بی‌طرف"
          count={summary.hold}
          tone="zinc"
          icon={Minus}
          hint="نمادهایی که شرایط بازار براشون مشخص نیست و اندیکاتورها سیگنال خرید یا فروش نمی‌دن. معمولاً بازار آروم یا در حال انتظار."
        />
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

      {/* Active filter banner */}
      {(filters.signal !== "all" || filters.strength !== "all") && (
        <Card className="border-purple-500/20 bg-purple-500/[0.03]">
          <CardContent className="flex flex-wrap items-center justify-between gap-2 py-2.5">
            <div className="flex items-center gap-2 text-xs">
              <Filter className="h-3.5 w-3.5 text-purple-400" />
              <span className="text-muted-foreground">فیلتر فعال:</span>
              <Badge
                variant="outline"
                className="border-purple-500/30 bg-purple-500/10 text-[10px] text-purple-300"
              >
                {filters.signal === "buy" && "خرید"}
                {filters.signal === "sell" && "فروش"}
                {filters.signal === "hold" && "بی‌طرف"}
                {filters.strength !== "all" &&
                  ` · ${
                    filters.strength === "strong"
                      ? "قوی"
                      : filters.strength === "medium"
                        ? "متوسط"
                        : "ضعیف"
                  }`}
              </Badge>
              <span className="text-[10px] text-muted-foreground/70">
                ({matches.length} نتیجه از {filteredMarkets.length} نماد)
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                setFilters({ ...filters, signal: "all", strength: "all" })
              }
              className="h-6 gap-1 px-2 text-[10px]"
            >
              <X className="h-3 w-3" />
              پاک کردن
            </Button>
          </CardContent>
        </Card>
      )}

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

          {!markets.isLoading && paginatedSignals.length === 0 && !isEmptyPage && (
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


// ---------- KPI Action Card ----------

const KPI_TONES = {
  emerald: {
    border: "border-emerald-500/20 hover:border-emerald-500/40",
    bg: "bg-emerald-500/[0.03] hover:bg-emerald-500/[0.06]",
    ring: "ring-emerald-500/40",
    text: "text-emerald-400",
  },
  red: {
    border: "border-red-500/20 hover:border-red-500/40",
    bg: "bg-red-500/[0.03] hover:bg-red-500/[0.06]",
    ring: "ring-red-500/40",
    text: "text-red-400",
  },
  amber: {
    border: "border-amber-500/20 hover:border-amber-500/40",
    bg: "bg-amber-500/[0.03] hover:bg-amber-500/[0.06]",
    ring: "ring-amber-500/40",
    text: "text-amber-400",
  },
  zinc: {
    border: "border-zinc-500/20 hover:border-zinc-500/40",
    bg: "bg-zinc-500/[0.03] hover:bg-zinc-500/[0.06]",
    ring: "ring-zinc-500/40",
    text: "text-zinc-400",
  },
} as const;

function KpiAction({
  label,
  count,
  breakdown,
  tone,
  icon: Icon,
  hint,
}: {
  label: string;
  count: number;
  breakdown?: { strong: number; medium: number; weak: number };
  tone: keyof typeof KPI_TONES;
  icon: React.ElementType;
  hint?: string;
}) {
  const t = KPI_TONES[tone];
  return (
    <div
      title={hint}
      className={cn(
        "cursor-help rounded-xl border p-4 text-right",
        t.border,
        t.bg,
      )}
    >
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4", t.text)} />
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
      <p className={cn("mt-1 font-mono text-2xl font-bold", t.text)}>{count}</p>
      {breakdown && count > 0 && (
        <p className="mt-1 font-mono text-[10px] text-muted-foreground/70">
          {breakdown.strong} قوی · {breakdown.medium} متوسط ·{" "}
          {breakdown.weak} ضعیف
        </p>
      )}
      {count === 0 && (
        <p className="mt-1 text-[10px] text-muted-foreground/50">—</p>
      )}
    </div>
  );
}
