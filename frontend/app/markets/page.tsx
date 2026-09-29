"use client";

import Link from "next/link";
import { TrendingUp, ArrowLeft } from "lucide-react";
import { useMarkets } from "@/lib/queries";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export default function MarketsPage() {
  const markets = useMarkets();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">بازارها</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {markets.data ? `${markets.data.count} نماد فعال` : "در حال بارگذاری..."}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            لیست نمادها
          </CardTitle>
          <CardDescription>
            روی هر نماد کلیک کنید تا دفتر سفارشات آن را ببینید
          </CardDescription>
        </CardHeader>
        <CardContent>
          {markets.isLoading ? (
            <div className="space-y-2">
              {[...Array(8)].map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {markets.data?.items.map((m) => (
                <Link
                  key={m.symbol}
                  href={`/markets/${m.symbol}`}
                  className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 transition hover:border-emerald-500/30 hover:bg-emerald-500/5"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-emerald-500/0 font-mono text-xs font-bold text-emerald-400">
                      {m.base_asset.slice(0, 3)}
                    </div>
                    <div>
                      <p className="font-mono text-sm font-semibold">{m.symbol}</p>
                      <p className="text-xs text-muted-foreground">
                        {m.fa_name ?? m.en_name ?? "—"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs">
                      {m.base_asset} / {m.quote_asset}
                    </Badge>
                    <ArrowLeft className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
