"use client";

import { useMemo, useState } from "react";
import { Check, ChevronsUpDown, Coins } from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";

interface SymbolComboboxProps {
  value: string;
  onChange: (symbol: string) => void;
  /** فیلتر بر اساس quote (پیش‌فرض: TMN) */
  quote?: string;
  placeholder?: string;
}

export function SymbolCombobox({
  value,
  onChange,
  quote = "TMN",
  placeholder = "انتخاب نماد...",
}: SymbolComboboxProps) {
  const [open, setOpen] = useState(false);
  const markets = useMarkets();

  // فیلتر و مرتب‌سازی بر اساس حجم معاملات (نزولی)
  const filteredMarkets = useMemo(() => {
    if (!markets.data?.items) return [];
    return markets.data.items
      .filter((m) => m.quote_asset === quote)
      .sort((a, b) => {
        // اولویت: daily_quote_volume (ارزش کل)، بعد daily_volume (مقدار)
        const volA = Number(a.daily_quote_volume || a.daily_volume || 0);
        const volB = Number(b.daily_quote_volume || b.daily_volume || 0);
        if (volB !== volA) return volB - volA;
        // در صورت تساوی: الفبایی
        return a.symbol.localeCompare(b.symbol);
      });
  }, [markets.data, quote]);

  // نماد انتخاب‌شده
  const selected = filteredMarkets.find((m) => m.symbol === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between font-mono text-sm"
          disabled={markets.isLoading}
        >
          {markets.isLoading ? (
            <span className="text-muted-foreground">در حال بارگذاری...</span>
          ) : selected ? (
            <span className="flex items-center gap-2">
              <span className="font-bold">{selected.base_asset}</span>
              <span className="text-muted-foreground text-xs">
                {selected.fa_name || selected.en_name}
              </span>
            </span>
          ) : value ? (
            <span>{value}</span>
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
          <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[--radix-popover-trigger-width] p-0"
        align="start"
      >
        <Command
          filter={(value, search) => {
            const v = value.toLowerCase();
            const s = search.toLowerCase();
            return v.includes(s) ? 1 : 0;
          }}
        >
          <CommandInput placeholder="جستجو بر اساس نماد یا نام..." />
          <CommandList className="max-h-[300px]">
            <CommandEmpty>
              <div className="py-6 text-center text-xs text-muted-foreground">
                نمادی پیدا نشد
              </div>
            </CommandEmpty>
            <CommandGroup>
              {filteredMarkets.map((m) => {
                // value برای جستجو: هم symbol و هم نام فارسی
                const searchKey = `${m.symbol} ${m.fa_name || ""} ${m.en_name || ""} ${m.base_asset}`;
                const isSelected = value === m.symbol;

                return (
                  <CommandItem
                    key={m.symbol}
                    value={searchKey}
                    onSelect={() => {
                      onChange(m.symbol);
                      setOpen(false);
                    }}
                    className={cn(
                      "flex items-center gap-2 cursor-pointer",
                      isSelected && "bg-emerald-500/10",
                    )}
                  >
                    <Check
                      className={cn(
                        "h-3.5 w-3.5 shrink-0 text-emerald-400",
                        isSelected ? "opacity-100" : "opacity-0",
                      )}
                    />
                    <Coins className="h-3.5 w-3.5 text-muted-foreground" />
                    <div className="flex flex-1 items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-bold">
                          {m.base_asset}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {m.fa_name || m.en_name}
                        </span>
                      </div>
                      {m.last_price && (
                        <span className="font-mono text-[10px] text-amber-400/70">
                          {Number(m.last_price).toLocaleString("en-US", {
                            maximumFractionDigits: 2,
                          })}
                        </span>
                      )}
                    </div>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </CommandList>
          <div className="border-t border-white/5 px-3 py-2 text-[10px] text-muted-foreground">
            {filteredMarkets.length} نماد در دسترس
          </div>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
