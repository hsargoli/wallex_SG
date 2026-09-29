"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowRight, TrendingUp } from "lucide-react";
import { useOrderBook } from "@/lib/queries";
import { formatNumber, formatPrice } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function SymbolPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = use(params);
  const book = useOrderBook(symbol);

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        <Link
          href="/markets"
          className="flex h-9 w-9 items-center justify-center rounded-lg border transition hover:border-emerald-500/30 hover:bg-emerald-500/5"
        >
          <ArrowRight className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="font-mono text-2xl font-bold tracking-tight">
            {symbol}
          </h1>
          <p className="text-sm text-muted-foreground">دفتر سفارشات زنده</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          {
            label: "بهترین خرید",
            value: book.data?.best_bid,
            accent: "text-emerald-400",
          },
          {
            label: "بهترین فروش",
            value: book.data?.best_ask,
            accent: "text-red-400",
          },
          {
            label: "اسپرد",
            value: book.data?.spread,
            accent: "text-amber-400",
          },
          {
            label: "اسپرد ٪",
            value: book.data?.spread_pct,
            accent: "text-purple-400",
          },
        ].map((item) => (
          <Card key={item.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">
                {item.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {book.isLoading ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                <p className={`font-mono text-xl font-bold ${item.accent}`}>
                  {item.value
                    ? item.label.includes("٪")
                      ? Number(item.value).toFixed(4)
                      : formatPrice(item.value)
                    : "—"}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <OrderBookTable
          title="خریداران (Bids)"
          levels={book.data?.bids ?? []}
          side="bid"
          loading={book.isLoading}
        />
        <OrderBookTable
          title="فروشندگان (Asks)"
          levels={book.data?.asks ?? []}
          side="ask"
          loading={book.isLoading}
        />
      </div>
    </div>
  );
}

function OrderBookTable({
  title,
  levels,
  side,
  loading,
}: {
  title: string;
  levels: { price: string; quantity: string; sum: string }[];
  side: "bid" | "ask";
  loading: boolean;
}) {
  const accent = side === "bid" ? "text-emerald-400" : "text-red-400";
  const barColor = side === "bid" ? "bg-emerald-500/10" : "bg-red-500/10";
  const maxSum = Math.max(...levels.map((l) => Number(l.sum) || 0), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className={`h-4 w-4 ${accent}`} />
          {title}
        </CardTitle>
        <CardDescription>{levels.length} سطح قیمت</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-1">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-7 w-full" />
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            <div className="grid grid-cols-3 gap-2 px-2 pb-2 text-[11px] text-muted-foreground">
              <span>قیمت</span>
              <span className="text-left">مقدار</span>
              <span className="text-left">مجموع</span>
            </div>
            {levels.slice(0, 15).map((lvl, i) => (
              <div
                key={i}
                className="relative grid grid-cols-3 gap-2 rounded px-2 py-1.5 font-mono text-xs"
              >
                <div
                  className={`absolute inset-y-0 right-0 rounded ${barColor}`}
                  style={{ width: `${(Number(lvl.sum) / maxSum) * 100}%` }}
                />
                <span className={`relative z-10 font-semibold ${accent}`}>
                  {formatPrice(lvl.price)}
                </span>
                <span className="relative z-10 text-left text-muted-foreground">
                  {formatNumber(lvl.quantity, { maximumFractionDigits: 4 })}
                </span>
                <span className="relative z-10 text-left text-muted-foreground">
                  {formatNumber(lvl.sum, { maximumFractionDigits: 0 })}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
