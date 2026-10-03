"use client";

import { useState } from "react";
import {
  ClipboardList,
  Plus,
  RefreshCw,
  XCircle,
  Loader2,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { useOrders, usePlaceOrder, useCancelOrder } from "@/lib/queries";
import { formatNumber, formatPrice } from "@/lib/format";
import type {
  Order,
  OrderSide,
  TradingOrderType,
} from "@/lib/api";
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

// ---------- PlaceOrder Dialog ----------

function PlaceOrderDialog() {
  const [open, setOpen] = useState(false);
  const [symbol, setSymbol] = useState("BTCTMN");
  const [side, setSide] = useState<OrderSide>("BUY");
  const [type, setType] = useState<TradingOrderType>("LIMIT");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");

  const placeOrder = usePlaceOrder();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quantity || Number(quantity) <= 0) return;
    if (type === "LIMIT" && (!price || Number(price) <= 0)) return;

    placeOrder.mutate(
      {
        symbol,
        side,
        type,
        quantity,
        price: type === "LIMIT" ? price : undefined,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setQuantity("");
          setPrice("");
        },
      },
    );
  };

  const totalValue =
    quantity && price ? Number(quantity) * Number(price) : 0;

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
            این یک سفارش <span className="font-bold text-amber-400">واقعی</span> روی
            صرافی والکس است.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>نماد معاملاتی</Label>
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCTMN"
              className="font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant={side === "BUY" ? "default" : "outline"}
              onClick={() => setSide("BUY")}
              className={cn(
                "gap-2",
                side === "BUY" && "bg-emerald-600 hover:bg-emerald-700",
              )}
            >
              <TrendingUp className="h-4 w-4" />
              خرید
            </Button>
            <Button
              type="button"
              variant={side === "SELL" ? "default" : "outline"}
              onClick={() => setSide("SELL")}
              className={cn(
                "gap-2",
                side === "SELL" && "bg-red-600 hover:bg-red-700",
              )}
            >
              <TrendingDown className="h-4 w-4" />
              فروش
            </Button>
          </div>

          <div className="space-y-2">
            <Label>نوع سفارش</Label>
            <Select value={type} onValueChange={(v) => setType(v as TradingOrderType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="LIMIT">Limit (قیمت مشخص)</SelectItem>
                <SelectItem value="MARKET">Market (قیمت بازار)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>مقدار ({symbol.replace("TMN", "") || "coin"})</Label>
            <Input
              type="text"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="0.00000884"
              className="font-mono"
            />
          </div>

          {type === "LIMIT" && (
            <div className="space-y-2">
              <Label>قیمت واحد (TMN)</Label>
              <Input
                type="text"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="11312379642"
                className="font-mono"
              />
            </div>
          )}

          {totalValue > 0 && (
            <div className="rounded-lg bg-black/30 border border-white/5 p-3">
              <p className="text-xs text-muted-foreground">مبلغ کل</p>
              <p className="text-lg font-mono font-bold text-amber-400">
                {formatNumber(totalValue)} TMN
              </p>
            </div>
          )}

          <Alert className="bg-amber-500/10 border-amber-500/30">
            <AlertDescription className="text-amber-300 text-xs leading-relaxed">
              ⚠️ این سفارش واقعی است. مطمئن شو قیمت و مقدار درسته.
            </AlertDescription>
          </Alert>

          <div className="flex gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              className="flex-1"
            >
              لغو
            </Button>
            <Button
              type="submit"
              disabled={placeOrder.isPending}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
            >
              {placeOrder.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "تأیید و ثبت"
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---------- Order Row ----------

function OrderRow({ order }: { order: Order }) {
  const cancelOrder = useCancelOrder();
  const isBuy = order.side === "BUY";

  const handleCancel = () => {
    if (!confirm(`لغو سفارش ${order.client_id}؟`)) return;
    cancelOrder.mutate({ clientId: order.client_id, symbol: order.symbol });
  };

  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
      <div className="flex flex-wrap items-center gap-3">
        {/* Side badge */}
        <Badge
          variant="outline"
          className={cn(
            "text-xs font-bold px-2 py-0.5 border",
            isBuy
              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
              : "bg-red-500/15 text-red-400 border-red-500/30",
          )}
        >
          {isBuy ? "خرید" : "فروش"}
        </Badge>

        {/* Symbol */}
        <div className="min-w-[100px]">
          <p className="font-mono text-sm font-bold">{order.symbol}</p>
          <p className="text-[10px] text-muted-foreground">{order.type}</p>
        </div>

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

        {/* Quantity */}
        <div className="min-w-[120px]">
          <p className="text-[10px] text-muted-foreground">مقدار</p>
          <p className="font-mono text-xs">
            {formatPrice(order.orig_qty)}
          </p>
        </div>

        {/* Price */}
        <div className="min-w-[140px]">
          <p className="text-[10px] text-muted-foreground">قیمت</p>
          <p className="font-mono text-xs">{formatNumber(order.price)} TMN</p>
        </div>

        {/* Executed */}
        {Number(order.executed_percent) > 0 && (
          <div className="min-w-[100px]">
            <p className="text-[10px] text-muted-foreground">اجرا</p>
            <p className="font-mono text-xs text-emerald-400">
              {formatNumber(order.executed_percent)}%
            </p>
          </div>
        )}

        {/* Cancel button */}
        <div className="mr-auto">
          {order.active ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={cancelOrder.isPending}
              className="gap-1 text-red-400 border-red-500/30 hover:bg-red-500/10"
            >
              {cancelOrder.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              لغو
            </Button>
          ) : (
            <p className="text-[10px] text-muted-foreground">
              {order.created_at > 0
                ? new Date(order.created_at * 1000).toLocaleDateString("fa-IR")
                : "—"}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------- Main Page ----------

export default function OrdersPage() {
  const [filterSymbol, setFilterSymbol] = useState("");
  const [appliedFilter, setAppliedFilter] = useState<string | undefined>();

  const orders = useOrders(appliedFilter);

  const handleRefresh = () => {
    orders.refetch();
  };

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
              variant="outline"
              onClick={handleRefresh}
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

      {/* Orders list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>
              {orders.data ? `${orders.data.count} سفارش` : "در حال بارگذاری..."}
            </span>
            {appliedFilter && (
              <span className="text-xs text-muted-foreground font-normal">
                فیلتر: {appliedFilter}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {orders.isLoading && (
            <>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
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

          {orders.data?.orders.map((order) => (
            <OrderRow key={order.client_id} order={order} />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
