"use client";

import { Search, X, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { QuoteFilter } from "@/components/markets/market-filters";

export type SignalTypeFilter = "all" | "buy" | "sell" | "hold";
export type StrengthFilter = "all" | "weak" | "medium" | "strong";

export interface SignalsFilterState {
  search: string;
  quote: QuoteFilter;
  signal: SignalTypeFilter;
  strength: StrengthFilter;
}

const SIGNAL_LABELS: Record<SignalTypeFilter, string> = {
  all: "همه سیگنال‌ها",
  buy: "خرید",
  sell: "فروش",
  hold: "بی‌طرف",
};

const STRENGTH_LABELS: Record<StrengthFilter, string> = {
  all: "همه قدرت‌ها",
  weak: "ضعیف",
  medium: "متوسط",
  strong: "قوی",
};

const QUOTE_LABELS: Record<QuoteFilter, string> = {
  all: "همه بازارها",
  TMN: "تومان (TMN)",
  USDT: "تتر (USDT)",
};

interface SignalsFilterProps {
  value: SignalsFilterState;
  onChange: (next: SignalsFilterState) => void;
  totalCount: number;
  filteredCount: number;
}

export function SignalsFilter({
  value,
  onChange,
  totalCount,
  filteredCount,
}: SignalsFilterProps) {
  const update = (patch: Partial<SignalsFilterState>) => {
    onChange({ ...value, ...patch });
  };

  const hasFilter =
    value.search.trim() !== "" ||
    value.quote !== "all" ||
    value.signal !== "all" ||
    value.strength !== "all";

  const clearAll = () => {
    onChange({
      search: "",
      quote: "all",
      signal: "all",
      strength: "all",
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={value.search}
            onChange={(e) => update({ search: e.target.value })}
            placeholder="جستجوی نماد..."
            className="pr-9"
          />
          {value.search && (
            <button
              onClick={() => update({ search: "" })}
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-white/5"
              aria-label="پاک کردن"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Quote */}
        <Select
          value={value.quote}
          onValueChange={(v) => update({ quote: v as QuoteFilter })}
        >
          <SelectTrigger className="w-[150px]">
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

        {/* Signal type */}
        <Select
          value={value.signal}
          onValueChange={(v) => update({ signal: v as SignalTypeFilter })}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(SIGNAL_LABELS) as SignalTypeFilter[]).map((k) => (
              <SelectItem key={k} value={k}>
                {SIGNAL_LABELS[k]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Strength */}
        <Select
          value={value.strength}
          onValueChange={(v) => update({ strength: v as StrengthFilter })}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(STRENGTH_LABELS) as StrengthFilter[]).map((k) => (
              <SelectItem key={k} value={k}>
                {STRENGTH_LABELS[k]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {hasFilter && (
          <Button variant="ghost" onClick={clearAll} className="gap-1 text-xs">
            <X className="h-3 w-3" />
            پاک کردن
          </Button>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>
          {filteredCount} از {totalCount} نماد در این صفحه
        </span>
      </div>
    </div>
  );
}
