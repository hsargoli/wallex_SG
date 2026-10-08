"use client";

import { Search, X, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import type { ScannerUrlState } from "@/lib/hooks/use-scanner-url-state";

const EMA_OPTS = [
  { value: "all", label: "همه EMA" },
  { value: "bullish", label: "EMA 9 > 21 (صعودی)" },
  { value: "bearish", label: "EMA 9 < 21 (نزولی)" },
];

const MACD_OPTS = [
  { value: "all", label: "همه MACD" },
  { value: "positive", label: "MACD مثبت" },
  { value: "negative", label: "MACD منفی" },
];

const BB_OPTS = [
  { value: "all", label: "همه باند" },
  { value: "low", label: "نزدیک کف (<20%)" },
  { value: "mid", label: "میانه (20-80%)" },
  { value: "high", label: "نزدیک سقف (>80%)" },
];

interface ScannerFiltersProps {
  state: ScannerUrlState;
  onUpdate: (patch: Partial<ScannerUrlState>) => void;
  onReset: () => void;
}

export function ScannerFilters({ state, onUpdate, onReset }: ScannerFiltersProps) {
  const hasFilter =
    state.search.trim() !== "" ||
    state.emaCross !== "all" ||
    state.macdSide !== "all" ||
    state.bbZone !== "all" ||
    state.rsiMin !== null ||
    state.rsiMax !== null ||
    state.atrMin !== null;

  return (
    <div className="space-y-3">
      {/* Row 1 */}
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

        <Select value={state.emaCross} onValueChange={(v) => onUpdate({ emaCross: v as ScannerUrlState["emaCross"], page: 1 })}>
          <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            {EMA_OPTS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={state.macdSide} onValueChange={(v) => onUpdate({ macdSide: v as ScannerUrlState["macdSide"], page: 1 })}>
          <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            {MACD_OPTS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={state.bbZone} onValueChange={(v) => onUpdate({ bbZone: v as ScannerUrlState["bbZone"], page: 1 })}>
          <SelectTrigger className="w-[170px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            {BB_OPTS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Row 2 */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-background/50 px-2 py-1">
          <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-muted-foreground">RSI:</span>
          <input
            type="number"
            value={state.rsiMin ?? ""}
            onChange={(e) => onUpdate({ rsiMin: e.target.value === "" ? null : Number(e.target.value), page: 1 })}
            placeholder="min"
            className="w-14 bg-transparent px-1 font-mono outline-none"
          />
          <span className="text-muted-foreground">—</span>
          <input
            type="number"
            value={state.rsiMax ?? ""}
            onChange={(e) => onUpdate({ rsiMax: e.target.value === "" ? null : Number(e.target.value), page: 1 })}
            placeholder="max"
            className="w-14 bg-transparent px-1 font-mono outline-none"
          />
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-background/50 px-2 py-1">
          <span className="text-muted-foreground">ATR% ≥</span>
          <input
            type="number"
            step="0.1"
            value={state.atrMin ?? ""}
            onChange={(e) => onUpdate({ atrMin: e.target.value === "" ? null : Number(e.target.value), page: 1 })}
            placeholder="2"
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
