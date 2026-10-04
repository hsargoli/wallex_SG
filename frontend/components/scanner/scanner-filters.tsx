"use client";

import { Search, X, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ScannerUrlState } from "@/lib/hooks/use-scanner-url-state";

const SIGNAL_OPTS = [
  { value: "all", label: "همه سیگنال‌ها" },
  { value: "buy", label: "خرید" },
  { value: "sell", label: "فروش" },
  { value: "hold", label: "بی‌طرف" },
];

const STRENGTH_OPTS = [
  { value: "all", label: "همه قدرت‌ها" },
  { value: "strong", label: "قوی" },
  { value: "medium", label: "متوسط" },
  { value: "weak", label: "ضعیف" },
];

interface ScannerFiltersProps {
  state: ScannerUrlState;
  onUpdate: (patch: Partial<ScannerUrlState>) => void;
  onReset: () => void;
}

export function ScannerFilters({ state, onUpdate, onReset }: ScannerFiltersProps) {
  const hasFilter =
    state.search.trim() !== "" ||
    state.signal !== "all" ||
    state.strength !== "all" ||
    state.rsiMin !== null ||
    state.rsiMax !== null ||
    state.rrMin !== null;

  return (
    <div className="space-y-3">
      {/* Row 1: search + selects */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={state.search}
            onChange={(e) => onUpdate({ search: e.target.value, page: 1 })}
            placeholder="جستجو بر اساس نماد..."
            className="pr-9"
          />
          {state.search && (
            <button
              onClick={() => onUpdate({ search: "" })}
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-white/5"
              aria-label="پاک کردن"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <Select
          value={state.signal}
          onValueChange={(v) => onUpdate({ signal: v, page: 1 })}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SIGNAL_OPTS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={state.strength}
          onValueChange={(v) => onUpdate({ strength: v, page: 1 })}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STRENGTH_OPTS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Row 2: numeric filters */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-background/50 px-2 py-1">
          <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-muted-foreground">RSI:</span>
          <input
            type="number"
            value={state.rsiMin ?? ""}
            onChange={(e) =>
              onUpdate({
                rsiMin: e.target.value === "" ? null : Number(e.target.value),
                page: 1,
              })
            }
            placeholder="min"
            className="w-14 bg-transparent px-1 font-mono outline-none"
          />
          <span className="text-muted-foreground">—</span>
          <input
            type="number"
            value={state.rsiMax ?? ""}
            onChange={(e) =>
              onUpdate({
                rsiMax: e.target.value === "" ? null : Number(e.target.value),
                page: 1,
              })
            }
            placeholder="max"
            className="w-14 bg-transparent px-1 font-mono outline-none"
          />
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-background/50 px-2 py-1">
          <span className="text-muted-foreground">R/R ≥</span>
          <input
            type="number"
            step="0.1"
            value={state.rrMin ?? ""}
            onChange={(e) =>
              onUpdate({
                rrMin: e.target.value === "" ? null : Number(e.target.value),
                page: 1,
              })
            }
            placeholder="1.5"
            className="w-14 bg-transparent px-1 font-mono outline-none"
          />
        </div>

        {hasFilter && (
          <Button variant="ghost" onClick={onReset} className="gap-1 text-xs">
            <X className="h-3 w-3" />
            پاک کردن فیلترها
          </Button>
        )}
      </div>
    </div>
  );
}
