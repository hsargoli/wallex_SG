"use client";

import { Search, X, ArrowUpDown, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// ---------- Types ----------

export type QuoteFilter = "all" | "TMN" | "USDT";

export type SortKey =
  | "volume"
  | "price"
  | "change"
  | "symbol"
  | "favorites_first";

export interface MarketFilterState {
  search: string;
  quote: QuoteFilter;
  sort: SortKey;
  showFavoritesOnly: boolean;
}

// ---------- Labels ----------

const SORT_LABELS: Record<SortKey, string> = {
  volume: "بیشترین حجم",
  price: "بالاترین قیمت",
  change: "بیشترین تغییر",
  symbol: "الفبایی",
  favorites_first: "علاقه‌مندی‌ها اول",
};

const QUOTE_LABELS: Record<QuoteFilter, string> = {
  all: "همه بازارها",
  TMN: "تومان (TMN)",
  USDT: "تتر (USDT)",
};

// ---------- Component ----------

interface MarketFiltersProps {
  value: MarketFilterState;
  onChange: (next: MarketFilterState) => void;
  totalCount: number;
  filteredCount: number;
  favoritesCount: number;
}

export function MarketFilters({
  value,
  onChange,
  totalCount,
  filteredCount,
  favoritesCount,
}: MarketFiltersProps) {
  const hasFilter =
    value.search.trim() !== "" ||
    value.quote !== "all" ||
    value.showFavoritesOnly;

  const update = (patch: Partial<MarketFilterState>) => {
    onChange({ ...value, ...patch });
  };

  const clearAll = () => {
    onChange({
      search: "",
      quote: "all",
      sort: value.sort,
      showFavoritesOnly: false,
    });
  };

  return (
    <div className="space-y-3">
      {/* Row 1: search + filter + sort */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={value.search}
            onChange={(e) => update({ search: e.target.value })}
            placeholder="جستجو بر اساس نماد یا نام..."
            className="pr-9"
          />
          {value.search && (
            <button
              onClick={() => update({ search: "" })}
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-white/5"
              aria-label="پاک کردن جستجو"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Quote filter */}
        <Select
          value={value.quote}
          onValueChange={(v) => update({ quote: v as QuoteFilter })}
        >
          <SelectTrigger className="w-[160px]">
            <Filter className="ml-1 h-3.5 w-3.5 text-muted-foreground" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(QUOTE_LABELS) as QuoteFilter[]).map((k) => (
              <SelectItem key={k} value={k}>
                {QUOTE_LABELS[k]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Sort */}
        <Select
          value={value.sort}
          onValueChange={(v) => update({ sort: v as SortKey })}
        >
          <SelectTrigger className="w-[170px]">
            <ArrowUpDown className="ml-1 h-3.5 w-3.5 text-muted-foreground" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(SORT_LABELS) as SortKey[]).map((k) => (
              <SelectItem key={k} value={k}>
                {SORT_LABELS[k]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Favorites toggle */}
        <Button
          variant={value.showFavoritesOnly ? "default" : "outline"}
          onClick={() =>
            update({ showFavoritesOnly: !value.showFavoritesOnly })
          }
          className={cn(
            "gap-1.5",
            value.showFavoritesOnly &&
              "bg-amber-600 hover:bg-amber-700 text-white",
          )}
        >
          <span className="text-base leading-none">⭐</span>
          علاقه‌مندی‌ها
          {favoritesCount > 0 && (
            <Badge
              variant="outline"
              className="border-white/20 bg-white/10 text-[10px]"
            >
              {favoritesCount}
            </Badge>
          )}
        </Button>

        {/* Clear */}
        {hasFilter && (
          <Button variant="ghost" onClick={clearAll} className="gap-1 text-xs">
            <X className="h-3 w-3" />
            پاک کردن فیلترها
          </Button>
        )}
      </div>

      {/* Row 2: stats */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>
          نمایش {filteredCount} از {totalCount} نماد
        </span>
        {value.showFavoritesOnly && (
          <Badge
            variant="outline"
            className="border-amber-500/30 bg-amber-500/10 text-[10px] text-amber-400"
          >
            فقط علاقه‌مندی‌ها
          </Badge>
        )}
      </div>
    </div>
  );
}
