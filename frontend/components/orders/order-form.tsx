"use client";

import { useState } from "react";
import { Loader2, TrendingDown, TrendingUp } from "lucide-react";
import { usePlaceOrder } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import type { OrderSide, TradingOrderType, PlaceOrderRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

const TYPE_LABELS: Record<TradingOrderType, string> = {
  LIMIT: "Limit (قیمت مشخص)",
  MARKET: "Market (قیمت بازار)",
  STOP_LIMIT: "Stop-Limit",
  STOP_MARKET: "Stop-Market",
};

const needsPrice = (t: TradingOrderType) => t === "LIMIT" || t === "STOP_LIMIT";
const needsStop = (t: TradingOrderType) => t === "STOP_LIMIT" || t === "STOP_MARKET";

type Errors = Partial<Record<"symbol" | "quantity" | "price" | "stop", string>>;

const positive = (v: string) => v.trim() !== "" && Number(v) > 0;

interface OrderFormProps {
  defaultSymbol?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function OrderForm({ defaultSymbol = "BTCTMN", onSuccess, onCancel }: OrderFormProps) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [side, setSide] = useState<OrderSide>("BUY");
  const [type, setType] = useState<TradingOrderType>("LIMIT");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [stopPrice, setStopPrice] = useState("");
  const [condition, setCondition] = useState<"<=" | ">=">("<=");
  const [errors, setErrors] = useState<Errors>({});
  const [reviewing, setReviewing] = useState(false);

  const placeOrder = usePlaceOrder();

  const total =
    needsPrice(type) && positive(quantity) && positive(price)
      ? Number(quantity) * Number(price)
      : 0;

  const validate = (): boolean => {
    const e: Errors = {};
    if (!symbol.trim()) e.symbol = "نماد را وارد کن";
    if (!positive(quantity)) e.quantity = "مقدار باید بزرگ‌تر از صفر باشد";
    if (needsPrice(type) && !positive(price)) e.price = "قیمت باید بزرگ‌تر از صفر باشد";
    if (needsStop(type) && !positive(stopPrice)) e.stop = "قیمت Stop باید بزرگ‌تر از صفر باشد";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleReview = (ev: React.FormEvent) => {
    ev.preventDefault();
    if (validate()) setReviewing(true);
  };

  const handleConfirm = () => {
    const payload: PlaceOrderRequest = {
      symbol: symbol.trim().toUpperCase(),
      side,
      type,
      quantity,
      ...(needsPrice(type) ? { price } : {}),
      ...(needsStop(type) ? { stop_price: stopPrice, stop_price_condition: condition } : {}),
    };
    placeOrder.mutate(payload, {
      onSuccess: () => {
        setQuantity("");
        setPrice("");
        setStopPrice("");
        setReviewing(false);
        onSuccess?.();
      },
    });
  };

  const rows: [string, string][] = [
    ["نماد", symbol.trim().toUpperCase()],
    ["سمت", side === "BUY" ? "خرید" : "فروش"],
    ["نوع", TYPE_LABELS[type]],
    ["مقدار", quantity],
    ...(needsPrice(type) ? ([["قیمت واحد", price + " TMN"]] as [string, string][]) : []),
    ...(needsStop(type)
      ? ([["قیمت Stop", `${stopPrice} TMN (شرط ${condition})`]] as [string, string][])
      : []),
    ...(total > 0 ? ([["مبلغ کل", formatNumber(total) + " TMN"]] as [string, string][]) : []),
  ];

  if (reviewing) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-white/10 divide-y divide-white/5">
          {rows.map(([k, v]) => (
            <div key={k} className="flex justify-between px-3 py-2 text-sm">
              <span className="text-muted-foreground">{k}</span>
              <span className="font-mono" dir="ltr">{v}</span>
            </div>
          ))}
        </div>
        <Alert className="bg-amber-500/10 border-amber-500/30">
          <AlertDescription className="text-amber-300 text-xs leading-relaxed">
            ⚠️ این سفارش واقعی است و روی والکس ثبت می‌شود. یک بار دیگر مقدار و قیمت را بررسی کن.
          </AlertDescription>
        </Alert>
        <div className="flex gap-2">
          <Button type="button" variant="outline" className="flex-1"
            onClick={() => setReviewing(false)} disabled={placeOrder.isPending}>
            بازگشت و ویرایش
          </Button>
          <Button type="button" className="flex-1 bg-emerald-600 hover:bg-emerald-700"
            onClick={handleConfirm} disabled={placeOrder.isPending}>
            {placeOrder.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "ثبت نهایی"}
          </Button>
        </div>
      </div>
    );
  }

  const err = (m?: string) => (m ? <p className="text-xs text-red-400">{m}</p> : null);

  return (
    <form onSubmit={handleReview} className="space-y-4">
      <div className="space-y-2">
        <Label>نماد معاملاتی</Label>
        <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="BTCTMN" className="font-mono" />
        {err(errors.symbol)}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button type="button" variant={side === "BUY" ? "default" : "outline"}
          onClick={() => setSide("BUY")}
          className={cn("gap-2", side === "BUY" && "bg-emerald-600 hover:bg-emerald-700")}>
          <TrendingUp className="h-4 w-4" />
          خرید
        </Button>
        <Button type="button" variant={side === "SELL" ? "default" : "outline"}
          onClick={() => setSide("SELL")}
          className={cn("gap-2", side === "SELL" && "bg-red-600 hover:bg-red-700")}>
          <TrendingDown className="h-4 w-4" />
          فروش
        </Button>
      </div>

      <div className="space-y-2">
        <Label>نوع سفارش</Label>
        <Select value={type} onValueChange={(v) => { setType(v as TradingOrderType); setErrors({}); }}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {(Object.keys(TYPE_LABELS) as TradingOrderType[]).map((t) => (
              <SelectItem key={t} value={t}>{TYPE_LABELS[t]}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>مقدار ({symbol.replace("TMN", "") || "coin"})</Label>
        <Input value={quantity} onChange={(e) => setQuantity(e.target.value)}
          placeholder="0.00000884" className="font-mono" />
        {err(errors.quantity)}
      </div>

      {needsStop(type) && (
        <div className="space-y-2">
          <Label>قیمت Stop (TMN)</Label>
          <div className="flex gap-2">
            <Select value={condition} onValueChange={(v) => setCondition(v as "<=" | ">=")}>
              <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="<=">{"<="}</SelectItem>
                <SelectItem value=">=">{">="}</SelectItem>
              </SelectContent>
            </Select>
            <Input value={stopPrice} onChange={(e) => setStopPrice(e.target.value)}
              className="font-mono" />
          </div>
          {err(errors.stop)}
        </div>
      )}

      {needsPrice(type) && (
        <div className="space-y-2">
          <Label>قیمت واحد (TMN)</Label>
          <Input value={price} onChange={(e) => setPrice(e.target.value)}
            placeholder="11312379642" className="font-mono" />
          {err(errors.price)}
        </div>
      )}

      {total > 0 && (
        <div className="rounded-lg bg-black/30 border border-white/5 p-3">
          <p className="text-xs text-muted-foreground">مبلغ کل</p>
          <p className="text-lg font-mono font-bold text-amber-400">{formatNumber(total)} TMN</p>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
            لغو
          </Button>
        )}
        <Button type="submit" className="flex-1 bg-emerald-600 hover:bg-emerald-700">
          بررسی سفارش
        </Button>
      </div>
    </form>
  );
}
