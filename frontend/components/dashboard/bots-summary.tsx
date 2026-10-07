"use client";

import Link from "next/link";
import { Bot, ArrowUpRight, Play, Square, TrendingUp, TrendingDown } from "lucide-react";
import { useBots, useBotStatus } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

// ---------- Row ----------

function BotRow({ slug, name, nameEn }: { slug: string; name: string; nameEn: string }) {
  const status = useBotStatus(slug);
  const isRunning = status.data?.is_running ?? false;
  const pnl: number | null = typeof status.data?.total_return_pct === "number" ? status.data.total_return_pct : null;
  const isPositive = (pnl ?? 0) >= 0;

  return (
    <Link
      href={`/bots/${slug}`}
      className="group flex items-center gap-3 rounded-lg border border-transparent px-3 py-2.5 transition-all hover:border-border hover:bg-white/[0.02]"
    >
      {/* Icon */}
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
          isRunning
            ? "bg-emerald-500/15 text-emerald-400"
            : "bg-white/5 text-muted-foreground",
        )}
      >
        <Bot className="h-4 w-4" />
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-medium">{name}</p>
          {isRunning ? (
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          ) : (
            <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
          )}
        </div>
        <p className="truncate text-[10px] text-muted-foreground">{nameEn}</p>
      </div>

      {/* PnL */}
      <div className="text-left">
        {status.isLoading ? (
          <Skeleton className="h-5 w-14" />
        ) : (
          <p
            className={cn(
              "font-mono text-xs font-bold",
              pnl === null || pnl === 0 ? "text-muted-foreground" : isPositive ? "text-emerald-400" : "text-red-400",
            )}
          >
            {pnl === null || pnl === 0 ? "—" : `${isPositive ? "+" : ""}${pnl.toFixed(2)}%`}
          </p>
        )}
        <p className="flex items-center justify-end gap-1 text-[10px] text-muted-foreground">
          {isRunning ? (
            <>
              <Play className="h-2.5 w-2.5" />
              فعال
            </>
          ) : (
            <>
              <Square className="h-2.5 w-2.5" />
              غیرفعال
            </>
          )}
        </p>
      </div>
    </Link>
  );
}

// ---------- Component ----------

export function BotsSummary() {
  const bots = useBots();

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-blue-400" />
            ربات‌های من
          </span>
          <Link href="/bots">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              مشاهده همه
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0.5">
        {bots.isLoading && (
          <>
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </>
        )}

        {bots.data?.bots.slice(0, 4).map((b) => (
          <BotRow key={b.slug} slug={b.slug} name={b.name} nameEn={b.name_en} />
        ))}

        {!bots.isLoading && (!bots.data?.bots || bots.data.bots.length === 0) && (
          <p className="py-8 text-center text-xs text-muted-foreground">
            رباتی ثبت نشده
          </p>
        )}
      </CardContent>
    </Card>
  );
}
