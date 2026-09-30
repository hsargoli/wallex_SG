"use client";

import { DollarSign, Coins, Lock } from "lucide-react";
import { useWallet } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export default function WalletPage() {
  const wallet = useWallet();
  const tmn = wallet.data?.items.find(
    (b) => b.asset === "TMN" || b.asset === "IRT",
  );
  const cryptos =
    wallet.data?.items.filter(
      (b) => b.asset !== "TMN" && b.asset !== "IRT",
    ) ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">کیف پول</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          موجودی لحظه‌ای حساب اصلی والکس
        </p>
      </div>

      {/* کارت تومان */}
      <Card className="relative overflow-hidden border-emerald-500/20">
        <div className="pointer-events-none absolute -left-16 -top-16 h-40 w-40 rounded-full bg-gradient-to-br from-emerald-500/20 to-emerald-500/0 blur-2xl" />
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <DollarSign className="h-5 w-5 text-emerald-400" />
            موجودی تومانی (TMN)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {wallet.isLoading ? (
            <Skeleton className="h-10 w-48" />
          ) : (
            <div className="space-y-2">
              <p className="font-mono text-3xl font-bold text-emerald-400">
                {formatNumber(tmn?.available ?? 0)} TMN
              </p>
              {tmn && Number(tmn.locked) > 0 && (
                <p className="flex items-center gap-1 text-xs text-amber-400">
                  <Lock className="h-3 w-3" />
                  فریز شده: {formatNumber(tmn.locked)} TMN
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* خلاصه */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              تعداد دارایی‌ها
            </CardTitle>
          </CardHeader>
          <CardContent>
            {wallet.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="font-mono text-2xl font-bold">
                {wallet.data?.count ?? 0}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              رمزارزها
            </CardTitle>
          </CardHeader>
          <CardContent>
            {wallet.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="font-mono text-2xl font-bold text-emerald-400">
                {cryptos.length}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              فریز شده
            </CardTitle>
          </CardHeader>
          <CardContent>
            {wallet.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="font-mono text-2xl font-bold text-amber-400">
                {
                  wallet.data?.items.filter((b) => Number(b.locked) > 0)
                    .length
                }
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* لیست رمزارزها */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Coins className="h-5 w-5 text-emerald-400" />
            دارایی‌های دیجیتال
          </CardTitle>
          <CardDescription>
            {wallet.data
              ? `${cryptos.length} رمزارز با موجودی غیرصفر`
              : "در حال بارگذاری..."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {wallet.isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : cryptos.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              هیچ رمزارزی با موجودی غیرصفر یافت نشد
            </p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {cryptos.map((b) => (
                <div
                  key={b.asset}
                  className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 transition hover:border-emerald-500/20 hover:bg-emerald-500/5"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-emerald-500/0 font-mono text-xs font-bold text-emerald-400">
                      {b.asset.slice(0, 3)}
                    </div>
                    <div>
                      <p className="font-mono text-sm font-semibold">
                        {b.asset}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {b.fa_name ?? "—"}
                      </p>
                    </div>
                  </div>
                  <div className="text-left">
                    <p className="font-mono text-sm font-semibold">
                      {formatNumber(b.available, {
                        maximumFractionDigits: 8,
                      })}
                    </p>
                    {Number(b.locked) > 0 && (
                      <Badge
                        variant="outline"
                        className="mt-1 border-amber-500/30 text-[10px] text-amber-400"
                      >
                        <Lock className="mr-1 h-2.5 w-2.5" />
                        {formatNumber(b.locked, {
                          maximumFractionDigits: 4,
                        })}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
