"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Wallet,
  ArrowUpRight,
} from "lucide-react";
import { usePortfolio, useBatchSignals, useCostBasis } from "@/lib/queries";
import type { BatchSignalItem, CostBasisItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const MAX_ROWS = 10;

const SIGNAL_CONFIG = {
  buy: {
    label: "خرید",
    icon: TrendingUp,
    text: "text-emerald-400",
    bg: "bg-emerald-500/15 border-emerald-500/30",
    rail: "border-r-emerald-500/50",
  },
  sell: {
    label: "فروش",
    icon: TrendingDown,
    text: "text-red-400",
    bg: "bg-red-500/15 border-red-500/30",
    rail: "border-r-red-500/50",
  },
  hold: {
    label: "بی‌طرف",
    icon: Minus,
    text: "text-zinc-400",
    bg: "bg-zinc-500/15 border-zinc-500/30",
    rail: "border-r-zinc-500/30",
  },
} as const;

/** قیمت دقیق با جداکننده هزارگان. مثال: 60,386 یا 308,684,400 */
function fmtPrice(v: number | string | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const n = typeof v === "string" ? Number(v) : v;
  if (!Number.isFinite(n)) return "—";
  const abs = Math.abs(n);
  if (abs >= 1) return new Intl.NumberFormat("en-US").format(Math.round(n));
  if (abs > 0) return n.toFixed(6);
  return "0";
}

/** مبلغ با علامت سود/ضرر + جداکننده */
function fmtSigned(n: number): string {
  const sign = n >= 0 ? "+" : "−";
  return `${sign}${new Intl.NumberFormat("en-US").format(Math.abs(Math.round(n)))}`;
}

/** مبلغ فشرده برای مقدار دارایی (برای حفظ فضای کم) */
function fmtCompact(v: number | string | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const n = typeof v === "string" ? Number(v) : v;
  if (!Number.isFinite(n) || n === 0) return "—";
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toFixed(0);
}

export function PortfolioSignals() {
  const portfolio = usePortfolio();
  const costBasis = useCostBasis();

  const allEntries = useMemo(() => {
    if (!portfolio.data?.items) return [];
    return portfolio.data.items
      .filter((it) => it.asset !== "TMN" && it.asset !== "IRT")
      .filter((it) => Number(it.total) > 0)
      .map((it) => ({
        item: it,
        symbol: it.has_tmn_pair
          ? `${it.asset}TMN`
          : it.has_usdt_pair
            ? `${it.asset}USDT`
            : null,
      }))
      .filter((e): e is { item: typeof e.item; symbol: string } => e.symbol !== null);
  }, [portfolio.data]);

  const entries = useMemo(
    () => allEntries.slice(0, MAX_ROWS),
    [allEntries],
  );

  const hiddenCount = Math.max(0, allEntries.length - MAX_ROWS);

  const symbols = useMemo(() => entries.map((e) => e.symbol), [entries]);
  const signals = useBatchSignals(symbols, "1h");

  const signalMap = useMemo(() => {
    const m = new Map<string, BatchSignalItem>();
    signals.data?.signals?.forEach((s) => m.set(s.symbol, s));
    return m;
  }, [signals.data]);

  const costMap = useMemo(() => {
    const m = new Map<string, CostBasisItem>();
    costBasis.data?.items?.forEach((c) => m.set(c.symbol, c));
    return m;
  }, [costBasis.data]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Wallet className="h-4 w-4 text-amber-400" />
          سیگنال دارایی‌های من
        </CardTitle>
        <Link
          href="/signals"
          className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          مشاهده همه
          <ArrowUpRight className="h-3 w-3" />
        </Link>
      </CardHeader>

      <CardContent className="space-y-1.5">
        {portfolio.isLoading && (
          <>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </>
        )}

        {!portfolio.isLoading && entries.length === 0 && (
          <div className="py-8 text-center">
            <Wallet className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              هنوز دارایی‌ای نداری
            </p>
          </div>
        )}

        {entries.map(({ item, symbol }) => {
          const sig = signalMap.get(symbol);
          const cb = costMap.get(symbol);
          const config = SIGNAL_CONFIG[sig?.signal ?? "hold"];
          const Icon = config.icon;

          const currentPrice = sig?.current_price ?? item.price_tmn_last;
          const avgBuy = cb?.avg_buy_price ?? null;
          const qty = Number(item.total);

          // سود/ضرر
          let pnlPct: number | null = null;
          let pnlTmn: number | null = null;
          let pnlLabel: string = "";

          if (avgBuy && currentPrice && qty > 0) {
            const avg = Number(avgBuy);
            const cur = Number(currentPrice);
            if (avg > 0) {
              pnlPct = ((cur - avg) / avg) * 100;
              pnlTmn = (cur - avg) * qty;
              if (pnlPct > 0.5) pnlLabel = "در سود هستی";
              else if (pnlPct < -0.5) pnlLabel = "در ضرر هستی";
              else pnlLabel = "تقریباً سر به سر";
            }
          }

          // متن tooltip — دقیق و کامل
          const tooltipText = cb
            ? [
                `💰 وضعیت: ${pnlLabel}`,
                "",
                `سود/ضرر فعلی: ${pnlPct !== null ? (pnlPct >= 0 ? "+" : "") + pnlPct.toFixed(2) + "%" : "—"}`,
                `مبلغ سود/ضرر: ${pnlTmn !== null ? fmtSigned(pnlTmn) + " TMN" : "—"}`,
                "",
                `میانگین خرید: ${fmtPrice(cb.avg_buy_price)} TMN`,
                `قیمت فعلی: ${fmtPrice(currentPrice)} TMN`,
                `مقدار دارایی: ${fmtPrice(qty)}`,
                `سرمایه‌گذاری: ${fmtPrice(cb.total_invested)} TMN`,
                "",
                `📊 ${cb.buy_count} بار خرید · ${cb.sell_count} بار فروش`,
              ].join("\n")
            : "خرید ثبت‌شده‌ای برای این دارایی نیست";

          return (
            <Link
              key={symbol}
              href={`/signals/${symbol}`}
              title={tooltipText}
              className={cn(
                "group grid grid-cols-[36px_1fr_80px_180px_90px] items-center gap-2.5 rounded-lg border border-border/50 border-r-2 bg-card px-3 py-2.5 transition-all hover:bg-muted/30",
                config.rail,
              )}
            >
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-md border",
                  config.bg,
                )}
              >
                {sig ? (
                  <Icon className={cn("h-3.5 w-3.5", config.text)} />
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
                )}
              </div>

              <div className="min-w-0">
                <p className="font-mono text-sm font-bold">{symbol}</p>
                {sig?.reasons?.[0] && (
                  <p className="truncate text-[10px] text-muted-foreground/80">
                    {sig.reasons[0]}
                  </p>
                )}
              </div>

              <p className="text-right font-mono text-[11px] text-muted-foreground">
                {fmtCompact(item.value_tmn_last)}
                <span className="mr-1 text-[9px] opacity-60">TMN</span>
              </p>

              {pnlPct !== null && pnlTmn !== null ? (
                <div className="text-right leading-tight">
                  <p
                    className={cn(
                      "font-mono text-sm font-bold",
                      pnlPct >= 0 ? "text-emerald-400" : "text-red-400",
                    )}
                  >
                    {pnlPct >= 0 ? "+" : ""}
                    {pnlPct.toFixed(1)}%
                  </p>
                  <p
                    className={cn(
                      "font-mono text-[10px]",
                      pnlTmn >= 0 ? "text-emerald-400/70" : "text-red-400/70",
                    )}
                  >
                    {fmtSigned(pnlTmn)} TMN
                  </p>
                </div>
              ) : (
                <p className="text-right font-mono text-[10px] text-muted-foreground/60">
                  {cb ? "خرید نامعلوم" : "بدون خرید"}
                </p>
              )}

              <div className="flex justify-end">
                {sig ? (
                  <Badge
                    variant="outline"
                    className={cn("border text-[10px]", config.bg, config.text)}
                  >
                    {config.label}
                  </Badge>
                ) : (
                  <span className="text-[10px] text-muted-foreground">—</span>
                )}
              </div>
            </Link>
          );
        })}

        {hiddenCount > 0 && (
          <Link
            href="/portfolio"
            className="mt-2 flex items-center justify-center gap-1 rounded-lg border border-dashed border-border/60 py-2 text-xs text-muted-foreground transition-all hover:border-amber-500/40 hover:bg-amber-500/[0.03] hover:text-amber-400"
          >
            <span>{hiddenCount} دارایی دیگر</span>
            <ArrowUpRight className="h-3 w-3" />
          </Link>
        )}
      </CardContent>
    </Card>
  );
}
