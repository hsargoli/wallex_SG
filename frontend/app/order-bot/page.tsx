"use client";

import { LiveModeBanner } from "@/components/orders/live-mode-banner";
import { ConfirmOrderDialog } from "@/components/order-bot/confirm-order-dialog";
import { useLiveMode } from "@/lib/hooks/use-live-mode";
import { useState } from "react";
import {
  Bot,
  Wallet,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Clock,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Loader2,
  Hash,
} from "lucide-react";
import {
  useOrders,
  useOpenOrders,
  usePlaceOrder,
  useCancelOrder,
} from "@/lib/queries";
import { formatNumber, formatPrice } from "@/lib/format";
import type { Order, OrderSide } from "@/lib/api";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { OrderBotChart } from "@/components/order-bot/order-bot-chart";
import { SymbolCombobox } from "@/components/order-bot/symbol-combobox";
import { formatTime } from "@/lib/format";

// ---------- Constants ----------

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
  STOP_LIMIT: "Stop-Limit",
  STOP_MARKET: "Stop-Market",
};

// ---------- Helpers ----------

// ---------- Order Form Component ----------

type OrderMode = "LIMIT" | "STOP_LIMIT";

interface OrderFormProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
}

function OrderForm({ symbol, onSymbolChange }: OrderFormProps) {
  const [side, setSide] = useState<OrderSide>("BUY");
  const [mode, setMode] = useState<OrderMode>("LIMIT");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [stopPrice, setStopPrice] = useState("");
  const [condition, setCondition] = useState<"<=" | ">=">("<=");

  const placeOrder = usePlaceOrder();
  type OrderPayload = Parameters<typeof placeOrder.mutate>[0];
  const [pending, setPending] = useState<OrderPayload | null>(null);
  const { liveOn, known, loading: modeLoading } = useLiveMode();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!liveOn) return;

    if (!quantity || Number(quantity) <= 0) return;
    if (!price || Number(price) <= 0) return;
    if (mode === "STOP_LIMIT" && (!stopPrice || Number(stopPrice) <= 0))
      return;

    const payload: Parameters<typeof placeOrder.mutate>[0] = {
      symbol,
      side,
      type: mode,
      quantity,
      price,
    };

    if (mode === "STOP_LIMIT") {
      payload.stop_price = stopPrice;
      payload.stop_price_condition = condition;
    }

    setPending(payload);
  };

  const confirmOrder = () => {
    if (!pending || !liveOn) return;
    placeOrder.mutate(pending, {
      onSuccess: () => {
        setQuantity("");
        setPrice("");
        setStopPrice("");
        setPending(null);
      },
      onError: () => setPending(null),
    });
  };

  const totalValue = quantity && price ? Number(quantity) * Number(price) : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Bot className="h-5 w-5 text-emerald-400" />
          ثبت سفارش دستی
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ConfirmOrderDialog
          payload={pending}
          busy={placeOrder.isPending}
          onConfirm={confirmOrder}
          onCancel={() => setPending(null)}
        />
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Symbol */}
          <div className="space-y-2">
            <Label>نماد معاملاتی</Label>
            <SymbolCombobox
              value={symbol}
              onChange={onSymbolChange}
              quote="TMN"
            />
          </div>

          {/* Mode selector */}
          <div className="space-y-2">
            <Label>نوع سفارش</Label>
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant={mode === "LIMIT" ? "default" : "outline"}
                onClick={() => setMode("LIMIT")}
                className={cn(
                  "gap-2",
                  mode === "LIMIT" && "bg-emerald-600 hover:bg-emerald-700",
                )}
              >
                <Clock className="h-4 w-4" />
                Limit
              </Button>
              <Button
                type="button"
                variant={mode === "STOP_LIMIT" ? "default" : "outline"}
                onClick={() => setMode("STOP_LIMIT")}
                className={cn(
                  "gap-2",
                  mode === "STOP_LIMIT" &&
                    "bg-amber-600 hover:bg-amber-700",
                )}
              >
                <ShieldAlert className="h-4 w-4" />
                Stop-Limit
              </Button>
            </div>
            {mode === "STOP_LIMIT" && (
              <p className="text-[10px] text-amber-400/80 leading-relaxed">
                ℹ️ در سفارش Stop-Limit، سرمایه شما فریز نمیشود تا وقتی قیمت
                به حد توقف برسد.
              </p>
            )}
          </div>

          {/* Side */}
          <div className="space-y-2">
            <Label>سمت سفارش</Label>
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
          </div>

          {/* Stop Price (فقط در STOP_LIMIT) */}
          {mode === "STOP_LIMIT" && (
            <>
              <div className="space-y-2">
                <Label className="text-amber-400">شرط فعالسازی</Label>
                <Select
                  value={condition}
                  onValueChange={(v) => setCondition(v as "<=" | ">=")}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="<=">قیمت ≤ حد توقف (کاهشی)</SelectItem>
                    <SelectItem value=">=">قیمت ≥ حد توقف (افزایشی)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-amber-400">
                  قیمت توقف (Stop Price)
                </Label>
                <Input
                  type="text"
                  value={stopPrice}
                  onChange={(e) => setStopPrice(e.target.value)}
                  placeholder="21000000000"
                  className="font-mono border-amber-500/30 focus:border-amber-500"
                />
                <p className="text-[10px] text-muted-foreground">
                  وقتی قیمت به این عدد رسید، سفارش فعال میشود
                </p>
              </div>
            </>
          )}

          {/* Limit Price */}
          <div className="space-y-2">
            <Label>
              {mode === "STOP_LIMIT"
                ? "قیمت سفارش (Limit Price)"
                : "قیمت واحد"}
            </Label>
            <Input
              type="text"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="22000000000"
              className="font-mono"
            />
          </div>

          {/* Quantity */}
          <div className="space-y-2">
            <Label>مقدار ({symbol.replace("TMN", "") || "coin"})</Label>
            <Input
              type="text"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="0.000004"
              className="font-mono"
            />
          </div>

          {/* Total value */}
          {totalValue > 0 && (
            <div className="rounded-lg bg-black/30 border border-white/5 p-3">
              <p className="text-xs text-muted-foreground">مبلغ کل (تقریبی)</p>
              <p className="text-lg font-mono font-bold text-amber-400">
                {formatNumber(totalValue)} TMN
              </p>
            </div>
          )}

          {!liveOn && !modeLoading && (
            <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-xs text-amber-700 dark:text-amber-300">
              {known
                ? "معامله‌ی واقعی غیرفعال است؛ ثبت سفارش قفل است."
                : "وضعیت معامله‌ی واقعی نامشخص است؛ ثبت سفارش تا روشن‌شدن وضعیت قفل است."}
            </p>
          )}

          {/* Submit */}
          <Button
            type="submit"
            disabled={placeOrder.isPending || !liveOn}
            className={cn(
              "w-full gap-2",
              mode === "LIMIT"
                ? "bg-emerald-600 hover:bg-emerald-700"
                : "bg-amber-600 hover:bg-amber-700",
            )}
          >
            {placeOrder.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                در حال ثبت...
              </>
            ) : (
              <>
                {side === "BUY" ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                ثبت سفارش {side === "BUY" ? "خرید" : "فروش"}
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

// ---------- Order Row Component ----------

function OrderRow({ order }: { order: Order }) {
  const cancelOrder = useCancelOrder();
  const isBuy = order.side === "BUY";
  const isStop = order.type.startsWith("STOP");

  const handleCancel = () => {
    if (!confirm(`لغو سفارش ${order.client_id}؟`)) return;
    cancelOrder.mutate({ clientId: order.client_id, symbol: order.symbol });
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-3 transition-all",
        isStop
          ? "border-amber-500/20 bg-amber-500/[0.03]"
          : "border-white/5 bg-white/[0.02]",
      )}
    >
      <div className="flex flex-wrap items-center gap-2 mb-2">
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

        <span className="font-mono text-sm font-bold">{order.symbol}</span>

        <Badge variant="outline" className="text-[10px] bg-white/5">
          {typeLabels[order.type] || order.type}
        </Badge>

        <Badge
          variant="outline"
          className={cn(
            "text-[10px]",
            statusColors[order.status] || statusColors.UNKNOWN,
          )}
        >
          {statusLabels[order.status] || order.status}
        </Badge>

        <div className="mr-auto">
          {order.active ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={cancelOrder.isPending}
              className="h-7 gap-1 text-red-400 border-red-500/30 hover:bg-red-500/10 text-xs"
            >
              {cancelOrder.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              لغو
            </Button>
          ) : (
            <span className="text-[10px] text-muted-foreground">
              {formatTime(order.created_at)}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <p className="text-[10px] text-muted-foreground">مقدار</p>
          <p className="font-mono">{formatPrice(order.orig_qty)}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground">قیمت</p>
          <p className="font-mono">{formatNumber(order.price)}</p>
        </div>
        {Number(order.stop_price) > 0 && (
          <div>
            <p className="text-[10px] text-amber-400">توقف</p>
            <p className="font-mono text-amber-300">
              {formatNumber(order.stop_price)}
            </p>
          </div>
        )}
      </div>

      <div className="mt-2 flex items-center gap-2 text-[10px] text-muted-foreground">
        <Hash className="h-3 w-3" />
        <span className="font-mono truncate">{order.client_id}</span>
      </div>
    </div>
  );
}

// ---------- Main Page ----------

export default function OrderBotPage() {
  const [symbol, setSymbol] = useState("BTCTMN");
  const openOrders = useOpenOrders();
  const historyOrders = useOrders();

  return (
    <div className="space-y-6">
      <LiveModeBanner />
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Bot className="h-6 w-6 text-emerald-400" />
            ثبت سفارش دستی
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            ثبت دستی سفارش‌های Limit و Stop-Limit روی صرافی والکس
          </p>
        </div>
        <div className="flex gap-2">
          <Badge
            variant="outline"
            className="border-emerald-500/30 text-emerald-400 bg-emerald-500/5 px-3 py-1.5"
          >
            <Wallet className="mr-1 h-3 w-3" />
            سفارش باز: {openOrders.data?.count ?? "—"}
          </Badge>
        </div>
      </div>

      {/* Chart */}
      <OrderBotChart symbol={symbol} />

      {/* Grid: Form + Orders */}
      <div className="grid gap-6 lg:grid-cols-[400px,1fr]">
        {/* Left: Form */}
        <OrderForm symbol={symbol} onSymbolChange={setSymbol} />

        {/* Right: Orders */}
        <div className="space-y-4">
          {/* Open Orders */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-emerald-400" />
                  سفارشات باز
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openOrders.refetch()}
                  disabled={openOrders.isFetching}
                  className="h-7 gap-1 text-xs"
                >
                  <RefreshCw
                    className={cn(
                      "h-3 w-3",
                      openOrders.isFetching && "animate-spin",
                    )}
                  />
                  بروزرسانی
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {openOrders.isLoading && <Skeleton className="h-20 w-full" />}

              {openOrders.isError && (
                <Alert className="bg-red-500/10 border-red-500/30">
                  <AlertDescription className="text-red-400 text-xs">
                    خطا در دریافت سفارشات باز
                  </AlertDescription>
                </Alert>
              )}

              {openOrders.data?.orders.length === 0 && (
                <div className="py-8 text-center">
                  <Clock className="mx-auto h-8 w-8 text-muted-foreground/30" />
                  <p className="mt-2 text-xs text-muted-foreground">
                    سفارش بازی ندارید
                  </p>
                </div>
              )}

              {openOrders.data?.orders.map((o) => (
                <OrderRow key={o.client_id} order={o} />
              ))}
            </CardContent>
          </Card>

          {/* History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CheckCircle2 className="h-5 w-5 text-blue-400" />
                آخرین سفارشات
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {historyOrders.isLoading && (
                <Skeleton className="h-20 w-full" />
              )}

              {historyOrders.data?.orders.length === 0 && (
                <p className="py-8 text-center text-xs text-muted-foreground">
                  سفارشی ثبت نشده
                </p>
              )}

              {historyOrders.data?.orders.slice(0, 5).map((o) => (
                <OrderRow key={o.client_id} order={o} />
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

