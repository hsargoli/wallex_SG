"use client";

import { useMemo, useState } from "react";
import {
  ClipboardList,
  Plus,
  RefreshCw,
  XCircle,
  Loader2,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  Ban,
  Hash,
} from "lucide-react";
import { useOrders, useOpenOrders, usePlaceOrder, useCancelOrder } from "@/lib/queries";
import { formatNumber, formatPrice } from "@/lib/format";
import type { Order, OrderSide, TradingOrderType } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { formatTime } from "@/lib/format";
import { OrderForm } from "@/components/orders/order-form";

// ---------- Helpers ----------

const statusLabels: Record<string, string> = {
  NEW: "فعال",
  PARTIALLY_FILLED: "نیمه‌پر",
  FILLED: "پر شده",
  CANCELED: "لغو شده",
  REJECTED: "رد شده",
  EXPIRED: "منقضی",
  UNKNOWN: "نامشخص",
};

const statusColors: Record<string, string> = {
  NEW: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  PARTIALLY_FILLED: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  FILLED: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  CANCELED: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  REJECTED: "bg-red-500/15 text-red-400 border-red-500/30",
  EXPIRED: "bg-zinc-500/15 text-zinc-500 border-zinc-500/30",
  UNKNOWN: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

const typeLabels: Record<string, string> = {
  LIMIT: "Limit",
  MARKET: "Market",
  STOP_LIMIT: "🛑 Stop-Limit",
  STOP_MARKET: "🛑 Stop-Market",
};

function computeTotal(order: Order): number {
  const qty = Number(order.orig_qty);
  const price = Number(order.price);
  return qty * price;
}

// ---------- Place Order Dialog ----------

function PlaceOrderDialog() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
          <Plus className="h-4 w-4" />
          سفارش جدید
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>ثبت سفارش جدید</DialogTitle>
          <DialogDescription>
            این یک سفارش{" "}
            <span className="font-bold text-amber-400">واقعی</span> روی صرافی
            والکس است.
          </DialogDescription>
        </DialogHeader>

        <OrderForm onSuccess={() => setOpen(false)} onCancel={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}

// ---------- Order Card ----------

function OrderCard({ order }: { order: Order }) {
  const cancelOrder = useCancelOrder();
  const isBuy = order.side === "BUY";
  const isActive = order.active;
  const executedPct = Number(order.executed_percent) || 0;
  const totalValue = computeTotal(order);

  const handleCancel = () => {
    if (!confirm(`لغو سفارش ${order.client_id}؟`)) return;
    cancelOrder.mutate({ clientId: order.client_id, symbol: order.symbol });
  };

  const isStop = order.type.startsWith("STOP");

  return (
    <div
      className={cn(
        "rounded-lg border p-4 transition-all",
        isStop && isActive
          ? "border-amber-500/30 bg-amber-500/[0.04] hover:bg-amber-500/[0.07]"
          : isActive
            ? "border-emerald-500/20 bg-emerald-500/[0.03] hover:bg-emerald-500/[0.06]"
            : "border-white/5 bg-white/[0.02] hover:bg-white/[0.04]",
      )}
    >
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-2.5 mb-3">
        {/* Side */}
        <Badge
          variant="outline"
          className={cn(
            "text-xs font-bold px-2 py-0.5 border gap-1",
            isBuy
              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
              : "bg-red-500/15 text-red-400 border-red-500/30",
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
        <span className="font-mono text-base font-bold">{order.symbol}</span>

        {/* Type */}
        <Badge
          variant="outline"
          className="text-[10px] bg-white/5 border-white/10"
        >
          {typeLabels[order.type] || order.type}
        </Badge>

        {/* Status */}
        <Badge
          variant="outline"
          className={cn(
            "text-[10px]",
            statusColors[order.status] || statusColors.UNKNOWN,
          )}
        >
          {statusLabels[order.status] || order.status}
        </Badge>

        {/* Cancel button */}
        <div className="mr-auto">
          {isActive ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={cancelOrder.isPending}
              className="gap-1.5 text-red-400 border-red-500/30 hover:bg-red-500/10 hover:text-red-300"
            >
              {cancelOrder.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <XCircle className="h-3.5 w-3.5" />
              )}
              لغو سفارش
            </Button>
          ) : (
            <span className="text-[10px] text-muted-foreground">
              {formatTime(order.created_at, true)}
            </span>
          )}
        </div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <p className="text-[10px] text-muted-foreground mb-0.5">مقدار</p>
          <p className="font-mono text-sm">{formatPrice(order.orig_qty)}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground mb-0.5">
            قیمت واحد
          </p>
          <p className="font-mono text-sm">
            {formatNumber(order.price)}{" "}
            <span className="text-[10px] text-muted-foreground">TMN</span>
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground mb-0.5">مبلغ کل</p>
          <p className="font-mono text-sm text-amber-400">
            {formatNumber(totalValue)}{" "}
            <span className="text-[10px] text-muted-foreground">TMN</span>
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground mb-0.5">
            اجرا شده
          </p>
          <p
            className={cn(
              "font-mono text-sm",
              executedPct >= 100
                ? "text-emerald-400"
                : executedPct > 0
                  ? "text-amber-400"
                  : "text-muted-foreground",
            )}
          >
            {executedPct.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Stop price (اگه > 0 بود) */}
      {Number(order.stop_price) > 0 && (
        <div className="mt-3 rounded-lg bg-amber-500/10 border border-amber-500/30 p-3">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs text-amber-400 font-bold flex items-center gap-1">
              🛑 قیمت توقف
            </span>
            <span className="font-mono text-sm text-amber-300 font-bold">
              {formatNumber(order.stop_price)} TMN
            </span>
            {order.stop_price_condition && (
              <span className="text-xs text-amber-400/80 font-mono">
                (شرط: {order.stop_price_condition})
              </span>
            )}
          </div>
          <p className="text-[10px] text-amber-400/60 mt-1 leading-relaxed">
            وقتی قیمت به {formatNumber(order.stop_price)} TMN برسه، سفارش
            فعال می‌شود.
          </p>
        </div>
      )}

      {/* Progress bar (اگر بخشی اجرا شده) */}
      {executedPct > 0 && executedPct < 100 && (
        <div className="mt-3 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-amber-500 to-emerald-500 transition-all"
            style={{ width: `${Math.min(executedPct, 100)}%` }}
          />
        </div>
      )}

      {/* Footer info */}
      <div className="mt-3 pt-3 border-t border-white/5 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <Hash className="h-3 w-3" />
          <span className="font-mono">{order.client_id}</span>
        </span>
        {order.created_at > 0 && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatTime(order.created_at, true)}
          </span>
        )}
        {Number(order.fee) > 0 && (
          <span>کارمزد: {formatNumber(order.fee)} TMN</span>
        )}
        {Number(order.executed_sum) > 0 && (
          <span>مبلغ اجرا: {formatNumber(order.executed_sum)} TMN</span>
        )}
      </div>
    </div>
  );
}

// ---------- Section ----------

function OrderSection({
  title,
  icon: Icon,
  iconColor,
  orders,
  defaultOpen = false,
}: {
  title: string;
  icon: React.ElementType;
  iconColor: string;
  orders: Order[];
  defaultOpen?: boolean;
}) {
  if (orders.length === 0) return null;

  return (
    <details open={defaultOpen} className="group">
      <summary className="flex cursor-pointer items-center gap-2 py-2 select-none list-none">
        <Icon className={cn("h-4 w-4", iconColor)} />
        <span className="text-sm font-bold">{title}</span>
        <Badge
          variant="outline"
          className="text-[10px] bg-white/5 border-white/10"
        >
          {orders.length}
        </Badge>
        <span className="mr-auto text-xs text-muted-foreground group-open:hidden">
          باز کن
        </span>
      </summary>
      <div className="space-y-2 mt-2">
        {orders.map((order) => (
          <OrderCard key={order.client_id} order={order} />
        ))}
      </div>
    </details>
  );
}

// ---------- Main Page ----------

export default function OrdersPage() {
  const [filterSymbol, setFilterSymbol] = useState("");
  const [appliedFilter, setAppliedFilter] = useState<string | undefined>();
  const [onlyActive, setOnlyActive] = useState(false);

  // داده اصلی: تاریخچه سفارشات
  const orders = useOrders(appliedFilter);
  // سفارشات باز فعلی (شامل STOP_LIMIT)
  const openOrders = useOpenOrders(appliedFilter);

  // گروه‌بندی سفارش‌ها
  const grouped = useMemo(() => {
    if (!orders.data?.orders && !openOrders.data?.orders) return null;

    const active: Order[] = [];
    const filled: Order[] = [];
    const closed: Order[] = [];

    // سفارشات تاریخچه
    for (const o of orders.data?.orders ?? []) {
      if (o.status === "NEW" || o.status === "PARTIALLY_FILLED") {
        active.push(o);
      } else if (o.status === "FILLED") {
        filled.push(o);
      } else {
        closed.push(o);
      }
    }

    // مرتب‌سازی نزولی بر اساس زمان ثبت
    const sortDesc = (arr: Order[]) =>
      arr.sort((a, b) => (b.created_at || 0) - (a.created_at || 0));

    const sortedActive = sortDesc(active);
    const sortedFilled = sortDesc(filled);
    const sortedClosed = sortDesc(closed);

    // آخرین ۵ سفارش (فقط FILLED یا PARTIALLY_FILLED — بدون لغو/رد شده)
    const allSorted = sortDesc([...orders.data?.orders ?? []]);
    const recent = allSorted
      .filter((o) => o.status === "FILLED" || o.status === "PARTIALLY_FILLED")
      .slice(0, 5);

    // سفارشات باز فعلی (از /open) — شامل STOP_LIMIT
    const openList = sortDesc(openOrders.data?.orders ?? []);
    const stopOrders = openList.filter((o) => o.type.startsWith("STOP"));
    const limitOpen = openList.filter((o) => !o.type.startsWith("STOP"));

    return {
      active: sortedActive,
      filled: sortedFilled,
      closed: sortedClosed,
      recent,
      openList,
      stopOrders,
      limitOpen,
    };
  }, [orders.data, openOrders.data]);

  const handleApplyFilter = () => {
    setAppliedFilter(filterSymbol.trim() || undefined);
  };

  const handleClearFilter = () => {
    setFilterSymbol("");
    setAppliedFilter(undefined);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <ClipboardList className="h-6 w-6 text-emerald-400" />
            سفارش‌های من
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            لیست سفارش‌های ثبت‌شده روی صرافی والکس
          </p>
        </div>
        <PlaceOrderDialog />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[200px] space-y-2">
              <Label htmlFor="filter-symbol">فیلتر بر اساس نماد</Label>
              <Input
                id="filter-symbol"
                value={filterSymbol}
                onChange={(e) => setFilterSymbol(e.target.value.toUpperCase())}
                placeholder="مثلاً BTCTMN (خالی = همه)"
                className="font-mono"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleApplyFilter();
                }}
              />
            </div>
            <Button onClick={handleApplyFilter} className="gap-2">
              اعمال فیلتر
            </Button>
            {appliedFilter && (
              <Button variant="outline" onClick={handleClearFilter}>
                پاک کردن
              </Button>
            )}
            <Button
              variant={onlyActive ? "default" : "outline"}
              onClick={() => setOnlyActive(!onlyActive)}
              className={cn(
                "gap-2",
                onlyActive && "bg-emerald-600 hover:bg-emerald-700",
              )}
            >
              <Clock className="h-4 w-4" />
              {onlyActive ? "نمایش همه" : "فقط فعال‌ها"}
            </Button>
            <Button
              variant="outline"
              onClick={() => orders.refetch()}
              disabled={orders.isFetching}
              className="gap-2"
            >
              <RefreshCw
                className={cn("h-4 w-4", orders.isFetching && "animate-spin")}
              />
              بروزرسانی
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats summary */}
      {grouped && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="bg-amber-500/[0.03] border-amber-500/20">
            <CardContent className="pt-4 pb-4">
              <p className="text-[10px] text-muted-foreground">سفارشات توقف</p>
              <p className="text-2xl font-mono font-bold text-amber-400">
                {grouped.stopOrders.length}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-emerald-500/[0.03] border-emerald-500/20">
            <CardContent className="pt-4 pb-4">
              <p className="text-[10px] text-muted-foreground">سفارشات باز</p>
              <p className="text-2xl font-mono font-bold text-emerald-400">
                {grouped.limitOpen.length}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-blue-500/[0.03] border-blue-500/20">
            <CardContent className="pt-4 pb-4">
              <p className="text-[10px] text-muted-foreground">پر شده</p>
              <p className="text-2xl font-mono font-bold text-blue-400">
                {grouped.filled.length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-[10px] text-muted-foreground">لغو/رد شده</p>
              <p className="text-2xl font-mono font-bold text-muted-foreground">
                {grouped.closed.length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-[10px] text-muted-foreground">مجموع</p>
              <p className="text-2xl font-mono font-bold">
                {orders.data?.count || 0}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Orders grouped */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            <span>سفارش‌ها</span>
            {appliedFilter && (
              <span className="text-xs text-muted-foreground font-normal">
                فیلتر: {appliedFilter}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {orders.isLoading && (
            <>
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </>
          )}

          {orders.isError && (
            <Alert className="bg-red-500/10 border-red-500/30">
              <AlertDescription className="text-red-400 text-sm">
                خطا در دریافت سفارش‌ها. اتصال به backend را بررسی کنید.
              </AlertDescription>
            </Alert>
          )}

          {orders.data && orders.data.orders.length === 0 && (
            <div className="py-12 text-center">
              <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-3 text-sm text-muted-foreground">
                سفارشی یافت نشد
              </p>
            </div>
          )}

          {grouped && (
            <>
              {/* STOP_LIMIT ها — همیشه اول (چون حساس‌ترین) */}
              {grouped.stopOrders.length > 0 && (
                <OrderSection
                  title="🛑 سفارشات توقف (Stop-Limit)"
                  icon={Ban}
                  iconColor="text-amber-400"
                  orders={grouped.stopOrders}
                  defaultOpen={false}
                />
              )}

              {/* LIMIT باز فعلی */}
              {grouped.limitOpen.length > 0 && (
                <OrderSection
                  title="⏱ سفارشات باز (Limit)"
                  icon={Clock}
                  iconColor="text-emerald-400"
                  orders={grouped.limitOpen}
                  defaultOpen={false}
                />
              )}

              {/* سفارشات فعال از تاریخچه */}
              {grouped.active.length > 0 && (
                <OrderSection
                  title="📋 سفارشات فعال (تاریخچه)"
                  icon={Clock}
                  iconColor="text-emerald-400"
                  orders={grouped.active}
                  defaultOpen={false}
                />
              )}

              {/* سفارشات اخیر — فقط اگه سفارش فعالی نیست */}
              {grouped.active.length === 0 && grouped.recent.length > 0 && (
                <OrderSection
                  title="🕐 آخرین سفارشات من"
                  icon={Clock}
                  iconColor="text-amber-400"
                  orders={grouped.recent}
                  defaultOpen={false}
                />
              )}

              <OrderSection
                title="✅ تکمیل شده"
                icon={CheckCircle2}
                iconColor="text-blue-400"
                orders={grouped.filled}
              />
              <OrderSection
                title="🚫 لغو / رد شده"
                icon={Ban}
                iconColor="text-zinc-500"
                orders={grouped.closed}
                defaultOpen={false}
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
