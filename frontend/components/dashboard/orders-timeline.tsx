"use client";

import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Ban,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ScrollText,
} from "lucide-react";
import { useOrders, useOpenOrders } from "@/lib/queries";
import { formatNumber, formatPrice } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { Order } from "@/lib/api";

// ---------- Configs ----------

const statusConfig: Record<
  string,
  {
    icon: React.ElementType;
    label: string;
    color: string;
    bg: string;
  }
> = {
  NEW: {
    icon: Clock,
    label: "در انتظار",
    color: "text-amber-400",
    bg: "bg-amber-500/15 border-amber-500/30",
  },
  PARTIALLY_FILLED: {
    icon: Clock,
    label: "نیمه‌پر",
    color: "text-blue-400",
    bg: "bg-blue-500/15 border-blue-500/30",
  },
  FILLED: {
    icon: CheckCircle2,
    label: "پر شده",
    color: "text-emerald-400",
    bg: "bg-emerald-500/15 border-emerald-500/30",
  },
  CANCELED: {
    icon: XCircle,
    label: "لغو شده",
    color: "text-zinc-400",
    bg: "bg-zinc-500/15 border-zinc-500/30",
  },
  REJECTED: {
    icon: Ban,
    label: "رد شده",
    color: "text-red-400",
    bg: "bg-red-500/15 border-red-500/30",
  },
  EXPIRED: {
    icon: Clock,
    label: "منقضی",
    color: "text-zinc-500",
    bg: "bg-zinc-500/15 border-zinc-500/30",
  },
  UNKNOWN: {
    icon: ScrollText,
    label: "نامشخص",
    color: "text-zinc-400",
    bg: "bg-zinc-500/15 border-zinc-500/30",
  },
};

const typeLabels: Record<string, string> = {
  LIMIT: "Limit",
  MARKET: "Market",
  STOP_LIMIT: "🛑 Stop-Limit",
  STOP_MARKET: "🛑 Stop-Market",
};

// ---------- Helpers ----------

function timeAgo(ts: number): string {
  if (!ts || ts <= 0) return "";
  const now = Math.floor(Date.now() / 1000);
  const diff = now - ts;
  if (diff < 60) return "الآن";
  if (diff < 3600) return `${Math.floor(diff / 60)} دقیقه پیش`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ساعت پیش`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} روز پیش`;
  return new Date(ts * 1000).toLocaleDateString("fa-IR");
}

// ---------- Row ----------

function OrderTimelineRow({ order }: { order: Order }) {
  const config = statusConfig[order.status] || statusConfig.UNKNOWN;
  const StatusIcon = config.icon;
  const isBuy = order.side === "BUY";
  const isStop = order.type.startsWith("STOP");

  return (
    <div className="relative flex gap-3 pb-4 last:pb-0">
      {/* Timeline dot + line */}
      <div className="relative flex flex-col items-center pt-1">
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
            config.bg,
          )}
        >
          <StatusIcon className={cn("h-4 w-4", config.color)} />
        </div>
        <div className="mt-1 w-px flex-1 bg-border/40" />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          {/* Side badge */}
          <Badge
            variant="outline"
            className={cn(
              "gap-1 text-[10px] font-bold",
              isBuy
                ? "border-emerald-500/30 bg-emerald-500/15 text-emerald-400"
                : "border-red-500/30 bg-red-500/15 text-red-400",
            )}
          >
            {isBuy ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {isBuy ? "خرید" : "فروش"}
          </Badge>

          {/* Symbol */}
          <span className="font-mono text-sm font-bold">{order.symbol}</span>

          {/* Type */}
          <Badge
            variant="outline"
            className={cn(
              "text-[10px]",
              isStop
                ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                : "bg-white/5",
            )}
          >
            {typeLabels[order.type] || order.type}
          </Badge>

          {/* Time */}
          <span className="mr-auto text-[10px] text-muted-foreground">
            {timeAgo(order.created_at)}
          </span>
        </div>

        {/* Details */}
        <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
          <span>
            <span className="text-muted-foreground">مقدار: </span>
            <span className="font-mono">{formatPrice(order.orig_qty)}</span>
          </span>
          <span>
            <span className="text-muted-foreground">قیمت: </span>
            <span className="font-mono">{formatNumber(order.price)}</span>
          </span>
          {Number(order.stop_price) > 0 && (
            <span className="text-amber-400">
              <span className="text-muted-foreground">توقف: </span>
              <span className="font-mono">
                {formatNumber(order.stop_price)}
              </span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------- Component ----------

export function OrdersTimeline() {
  const openOrders = useOpenOrders();
  const historyOrders = useOrders();

  // ترکیب: سفارشات باز اول، بعد تاریخچه
  const allOrders = [
    ...(openOrders.data?.orders || []),
    ...((historyOrders.data?.orders || []).filter((o) => !o.active)),
  ].slice(0, 8);

  const isLoading = openOrders.isLoading || historyOrders.isLoading;
  const openCount = openOrders.data?.count || 0;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-emerald-400" />
            آخرین سفارشات
            {openCount > 0 && (
              <Badge
                variant="outline"
                className="border-emerald-500/30 bg-emerald-500/15 text-[10px] text-emerald-400"
              >
                {openCount} باز
              </Badge>
            )}
          </span>
          <Link href="/orders">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              مشاهده همه
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        )}

        {!isLoading && allOrders.length === 0 && (
          <div className="py-8 text-center">
            <ScrollText className="mx-auto h-10 w-10 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              هنوز سفارشی ثبت نشده
            </p>
            <Link href="/order-bot">
              <Button variant="outline" size="sm" className="mt-3">
                ثبت اولین سفارش
              </Button>
            </Link>
          </div>
        )}

        {!isLoading && allOrders.length > 0 && (
          <div className="space-y-0">
            {allOrders.map((o) => (
              <OrderTimelineRow key={o.client_id} order={o} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
