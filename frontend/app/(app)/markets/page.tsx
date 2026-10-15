"use client";

import { useEffect, useMemo, useState } from "react";
import { TrendingUp, List, LayoutGrid } from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { useFavorites } from "@/lib/hooks/use-favorites";
import {
  MarketFilters,
  type MarketFilterState,
  type QuoteFilter,
  type SortKey,
} from "@/components/markets/market-filters";
import { MarketRow } from "@/components/markets/market-row";
import { MarketCard } from "@/components/markets/market-card";
import { MarketPagination } from "@/components/markets/market-pagination";
import {
  ViewToggle,
  type ViewMode,
} from "@/components/markets/view-toggle";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 30;

// ---------- localStorage keys ----------
const LS_VIEW = "wallex-markets-view";
const LS_SORT = "wallex-markets-sort";
const LS_QUOTE = "wallex-markets-quote";

// ---------- Component ----------

export default function MarketsPage() {
  const markets = useMarkets();
  const { favorites, toggle, isFavorite } = useFavorites();

  // UI state
  const [view, setView] = useState<ViewMode>("list");
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<MarketFilterState>({
    search: "",
    quote: "all",
    sort: "volume",
    showFavoritesOnly: false,
  });

  // Load saved preferences on mount
  useEffect(() => {
    try {
      const savedView = localStorage.getItem(LS_VIEW) as ViewMode | null;
      if (savedView === "list" || savedView === "grid") setView(savedView);

      const savedSort = localStorage.getItem(LS_SORT) as SortKey | null;
      if (savedSort) setFilters((f) => ({ ...f, sort: savedSort }));

      const savedQuote = localStorage.getItem(LS_QUOTE) as QuoteFilter | null;
      if (savedQuote) setFilters((f) => ({ ...f, quote: savedQuote }));
    } catch {
      // ignore
    }
  }, []);

  // Persist view
  const handleViewChange = (v: ViewMode) => {
    setView(v);
    try {
      localStorage.setItem(LS_VIEW, v);
    } catch {
      // ignore
    }
  };

  // Persist filters when they change
  const handleFiltersChange = (next: MarketFilterState) => {
    setFilters(next);
    setPage(1); // reset page on filter change
    try {
      localStorage.setItem(LS_SORT, next.sort);
      localStorage.setItem(LS_QUOTE, next.quote);
    } catch {
      // ignore
    }
  };

  // ---------- Filtered + sorted markets ----------
  const filtered = useMemo(() => {
    if (!markets.data?.items) return [];

    const search = filters.search.trim().toLowerCase();

    let list = markets.data.items.filter((m) => {
      // Quote filter
      if (filters.quote !== "all" && m.quote_asset !== filters.quote) {
        return false;
      }
      // Favorites only
      if (filters.showFavoritesOnly && !favorites.includes(m.symbol)) {
        return false;
      }
      // Search
      if (search) {
        const haystack = [
          m.symbol,
          m.base_asset,
          m.quote_asset,
          m.fa_name || "",
          m.en_name || "",
        ]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(search)) return false;
      }
      return true;
    });

    // Sort
    list = [...list].sort((a, b) => {
      // Favorites first is special
      if (filters.sort === "favorites_first") {
        const aFav = favorites.includes(a.symbol);
        const bFav = favorites.includes(b.symbol);
        if (aFav !== bFav) return aFav ? -1 : 1;
        // fallback to volume
        return (
          Number(b.daily_quote_volume || 0) -
          Number(a.daily_quote_volume || 0)
        );
      }

      switch (filters.sort) {
        case "volume":
          return (
            Number(b.daily_quote_volume || 0) -
            Number(a.daily_quote_volume || 0)
          );
        case "price":
          return Number(b.last_price || 0) - Number(a.last_price || 0);
        case "change":
          return (
            Number(b.daily_change_percent || 0) -
            Number(a.daily_change_percent || 0)
          );
        case "symbol":
          return a.symbol.localeCompare(b.symbol);
        default:
          return 0;
      }
    });

    return list;
  }, [markets.data, filters, favorites]);

  // ---------- Pagination ----------
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginated = filtered.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE,
  );

  const totalCount = markets.data?.count || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <TrendingUp className="h-6 w-6 text-emerald-400" />
            بازارها
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {markets.isLoading
              ? "در حال بارگذاری..."
              : `${totalCount} نماد فعال`}
          </p>
        </div>
        <ViewToggle value={view} onChange={handleViewChange} />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <MarketFilters
            value={filters}
            onChange={handleFiltersChange}
            totalCount={totalCount}
            filteredCount={filtered.length}
            favoritesCount={favorites.length}
          />
        </CardContent>
      </Card>

      {/* Markets */}
      {markets.isLoading && (
        <div
          className={cn(
            view === "list"
              ? "space-y-2"
              : "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4",
          )}
        >
          {[...Array(8)].map((_, i) => (
            <Skeleton
              key={i}
              className={view === "list" ? "h-16 w-full" : "h-40 w-full"}
            />
          ))}
        </div>
      )}

      {!markets.isLoading && filtered.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white/5">
              {view === "list" ? (
                <List className="h-6 w-6 text-muted-foreground/50" />
              ) : (
                <LayoutGrid className="h-6 w-6 text-muted-foreground/50" />
              )}
            </div>
            <p className="text-sm font-medium">نمادی پیدا نشد</p>
            <p className="mt-1 text-xs text-muted-foreground">
              فیلترها را تغییر دهید یا جستجو را پاک کنید
            </p>
          </CardContent>
        </Card>
      )}

      {!markets.isLoading && paginated.length > 0 && (
        <>
          {view === "list" ? (
            <div className="space-y-1.5">
              {paginated.map((m) => (
                <MarketRow
                  key={m.symbol}
                  market={m}
                  isFavorite={isFavorite(m.symbol)}
                  onToggleFavorite={toggle}
                />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {paginated.map((m) => (
                <MarketCard
                  key={m.symbol}
                  market={m}
                  isFavorite={isFavorite(m.symbol)}
                  onToggleFavorite={toggle}
                />
              ))}
            </div>
          )}

          <MarketPagination
            page={safePage}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
