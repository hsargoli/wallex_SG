"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState } from "react";
import { Wallet, DollarSign, TrendingUp, Percent } from "lucide-react";
import { usePortfolio } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { PortfolioTable } from "@/components/portfolio/portfolio-table";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

type PriceSource = "bid" | "last";

function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  accent,
  loading,
}: {
  title: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  accent: string;
  loading?: boolean;
}) {
  return (
    <Card className="relative overflow-hidden">
      <div className="pointer-events-none absolute -left-16 -top-16 h-40 w-40 rounded-full bg-gradient-to-br from-emerald-500/10 to-emerald-500/0 blur-2xl" />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className={`h-4 w-4 ${accent}`} />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-32" />
        ) : (
          <div className={`font-mono text-2xl font-bold ${accent}`}>
            {value}
          </div>
        )}
        {sub && (
          <p className="mt-1 font-mono text-[11px] text-muted-foreground">
            {sub}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function ConcentrationAlert({ items, isBid }: { items: any[]; isBid: boolean }) {
  const vals = items
    .map((it) => ({ a: String(it.asset ?? it.symbol ?? "?"), v: Number(isBid ? it.value_tmn_bid : it.value_tmn_last) || 0 }))
    .filter((x) => x.v > 0)
    .sort((x, y) => y.v - x.v);
  const total = vals.reduce((a, x) => a + x.v, 0);
  if (total <= 0 || vals.length < 3) return null;
  const top = vals.slice(0, 3);
  const pct = (top.reduce((a, x) => a + x.v, 0) / total) * 100;
  if (pct < 60) return null;
  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
      <b>تمرکز ریسک:</b> سه دارایی بزرگ ({top.map((x) => x.a).join("، ")}) روی هم {pct.toFixed(1)}٪ سبد را می‌سازند.
    </div>
  );
}

export default function PortfolioPage() {
  const portfolio = usePortfolio();
  const [priceSource, setPriceSource] = useState<PriceSource>("bid");
  const [hideDust, setHideDust] = useState(false);

  const data = portfolio.data;
  const items = data?.items ?? [];
  const isBid = priceSource === "bid";

  const totalTmn = isBid
    ? data?.total_value_tmn_bid
    : data?.total_value_tmn_last;
  const totalUsdt = isBid
    ? data?.total_value_usdt_bid
    : data?.total_value_usdt_last;

  const visibleItems = hideDust
    ? items.filter((it) => {
        const v = isBid ? it.value_tmn_bid : it.value_tmn_last;
        return Number(v ?? 0) >= 10000;
      })
    : items;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">سبد دارایی</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            ارزش‌گذاری کامل دارایی‌ها به تتر و تومان
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle قیمت */}
          <div className="flex items-center gap-1 rounded-lg border bg-card p-1">
            <button
              onClick={() => setPriceSource("bid")}
              className={`rounded px-3 py-1.5 text-xs font-medium transition ${
                isBid
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              💰 ارزش برداشت
              <span className="mr-1 opacity-60">(bid)</span>
            </button>
            <button
              onClick={() => setPriceSource("last")}
              className={`rounded px-3 py-1.5 text-xs font-medium transition ${
                !isBid
                  ? "bg-blue-500/20 text-blue-400"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              📊 ارزش اسمی
              <span className="mr-1 opacity-60">(last)</span>
            </button>
          </div>

          {/* پنهان کردن ریزها */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setHideDust((v) => !v)}
          >
            {hideDust ? "نمایش ریزها" : "پنهان کردن ریزها"}
          </Button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={isBid ? "ارزش قابل برداشت" : "ارزش اسمی"}
          value={formatNumber(totalTmn ?? 0, { maximumFractionDigits: 0 })}
          sub={`≈ $${formatNumber(totalUsdt ?? 0, { maximumFractionDigits: 2 })} — ${isBid ? "bid price" : "last price"}`}
          icon={Wallet}
          accent={isBid ? "text-emerald-400" : "text-blue-400"}
          loading={portfolio.isLoading}
        />
        <StatCard
          title="ارزش دلاری"
          value={`$${formatNumber(totalUsdt ?? 0, { maximumFractionDigits: 2 })}`}
          sub="معادل دلاری سبد"
          icon={DollarSign}
          accent="text-blue-400"
          loading={portfolio.isLoading}
        />
        <StatCard
          title="نرخ USDT/TMN"
          value={formatNumber(data?.usdt_tmn_rate ?? 0, {
            maximumFractionDigits: 0,
          })}
          sub="نرخ لحظه‌ای والکس"
          icon={Percent}
          accent="text-purple-400"
          loading={portfolio.isLoading}
        />
        <StatCard
          title="تعداد دارایی"
          value={`${data?.count ?? 0}`}
          sub={`${visibleItems.length} مورد نمایش`}
          icon={TrendingUp}
          accent="text-amber-400"
          loading={portfolio.isLoading}
        />
      </div>

      <ConcentrationAlert items={visibleItems as any[]} isBid={isBid} />

      {/* Table */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">
          ریز دارایی‌ها
          <span className="mr-2 text-xs font-normal text-muted-foreground">
            (مرتب بر اساس {isBid ? "ارزش برداشت" : "ارزش اسمی"})
          </span>
        </h2>
        {portfolio.isLoading ? (
          <div className="space-y-2">
            {[...Array(8)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <PortfolioTable items={visibleItems} priceSource={priceSource} />
        )}
      </div>
    </div>
  );
}
