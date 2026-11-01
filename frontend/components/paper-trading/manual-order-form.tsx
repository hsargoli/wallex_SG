/**
 * Manual Order Form — فرم سفارش دستی (symbol, amount, limit, TP/SL, submit).
 * DRY ManualOrderForm — Phase 2.
 *
 * Props are fully controlled — parent owns state and mutation.
 */
"use client";

import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { SYMBOLS } from "./symbols";
import { formatNum, parseNum, fmt } from "@/lib/paper-format";

export type ManualOrderFormProps = {
  /** آیا Paper در حال اجرا است؟ (form disabled if not) */
  isRunning: boolean;
  /** موجودی (نقد) */
  capital: number;
  /** تعداد پوزیشن‌های باز (برای cap ۱۰) */
  openPositionsCount?: number;
  /** قیمت بازار (برای نمایش) */
  marketPrice: { data?: { price: number | null } | null; isLoading: boolean };
  /** فرم state (controlled) */
  orderSymbol: string;
  orderAmount: string;
  orderTp: string;
  orderSl: string;
  orderLimitPrice: string;
  /** setters */
  setOrderSymbol: (s: string) => void;
  setOrderAmount: (s: string) => void;
  setOrderTp: (s: string) => void;
  setOrderSl: (s: string) => void;
  setOrderLimitPrice: (s: string) => void;
  /** submit */
  onSubmit: () => void;
  isSubmitting: boolean;
  /** variant */
  variant?: "guest" | "user";
};

export function ManualOrderForm({
  isRunning,
  capital,
  openPositionsCount = 0,
  marketPrice,
  orderSymbol,
  orderAmount,
  orderTp,
  orderSl,
  orderLimitPrice,
  setOrderSymbol,
  setOrderAmount,
  setOrderTp,
  setOrderSl,
  setOrderLimitPrice,
  onSubmit,
  isSubmitting,
  variant = "user",
}: ManualOrderFormProps) {
  return (
    <Card className="border-violet-500/15 bg-background/60">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="h-5 w-5 text-violet-400" />
          ثبت سفارش دستی
          {variant === "guest" && (
            <span className="text-xs text-muted-foreground">(شبیه‌سازی)</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!isRunning && (
          <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            {variant === "guest"
              ? "ابتدا دکمه‌ی شروع را بزن."
              : "ابتدا دکمه‌ی «شروع Paper» را بزن."}
          </div>
        )}

        {/* Side (buy only for MVP) */}
        <div className="grid grid-cols-2 gap-2">
          <div className="col-span-2 rounded-lg border-2 border-emerald-500 bg-emerald-500/20 py-2 text-center text-sm font-bold text-emerald-300">
            خرید دارایی
          </div>
        </div>

        {/* Symbol */}
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">نماد</Label>
          <div className="flex flex-wrap gap-1">
            {SYMBOLS.map((s) => (
              <button
                key={s.key}
                onClick={() => setOrderSymbol(s.key)}
                type="button"
                className={cn(
                  "rounded-full border px-3 py-1 text-[10px] font-medium transition",
                  s.key === orderSymbol
                    ? "border-violet-500 bg-violet-600 text-white"
                    : "border-white/10 text-muted-foreground hover:border-violet-500/40",
                )}
              >
                {s.fa}
              </button>
            ))}
          </div>
        </div>

        {/* Amount */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-muted-foreground">مبلغ (تومان)</Label>
            <span className="font-mono text-[10px] text-muted-foreground">
              موجودی: {fmt(capital)}
            </span>
          </div>
          <Input
            type="text"
            inputMode="numeric"
            value={orderAmount}
            onChange={(e) => setOrderAmount(formatNum(e.target.value))}
            placeholder="۱۰۰٬۰۰۰"
            className="h-10 font-mono text-sm"
            disabled={!isRunning}
          />
          <div className="flex gap-1">
            {[25, 50, 75, 100].map((pct) => {
              const amount = Math.floor(capital * (pct / 100));
              const active = parseNum(orderAmount) === String(amount);
              return (
                <button
                  key={pct}
                  onClick={() => setOrderAmount(formatNum(String(amount)))}
                  type="button"
                  disabled={!isRunning}
                  className={cn(
                    "flex-1 rounded-md border px-2 py-1 text-[10px] font-medium transition",
                    active
                      ? "border-violet-500 bg-violet-600/20 text-violet-300"
                      : "border-white/10 text-muted-foreground hover:border-violet-500/40",
                    !isRunning && "opacity-50 cursor-not-allowed",
                  )}
                >
                  {pct}٪
                </button>
              );
            })}
          </div>
        </div>

        {/* Limit */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-muted-foreground">
              قیمت پیشنهادی (اختیاری)
            </Label>
            <span className="font-mono text-[10px]">
              {marketPrice.isLoading ? (
                <span className="text-muted-foreground">...</span>
              ) : marketPrice.data?.price ? (
                <span className="text-violet-300">
                  بازار: {fmt(marketPrice.data.price)}
                </span>
              ) : (
                <span className="text-rose-400">قیمت موجود نیست</span>
              )}
            </span>
          </div>
          <Input
            type="text"
            inputMode="numeric"
            value={orderLimitPrice}
            onChange={(e) => setOrderLimitPrice(formatNum(e.target.value))}
            placeholder="خالی = قیمت بازار"
            className="h-9 font-mono text-xs"
            disabled={!isRunning}
          />
          {orderLimitPrice && marketPrice.data?.price && (() => {
            const lp = parseFloat(parseNum(orderLimitPrice));
            const mp = marketPrice.data.price!;
            const ok = lp >= mp;
            return (
              <p className={cn(
                "text-[10px]",
                ok ? "text-emerald-400" : "text-amber-400",
              )}>
                {ok
                  ? "✅ قیمت شما ≥ بازار — سفارش پذیرفته می‌شه"
                  : "⚠️ قیمت شما < بازار — سفارش رد می‌شه"}
              </p>
            );
          })()}
        </div>

        {/* TP/SL */}
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">TP (٪ سود)</Label>
            <Input
              value={orderTp}
              onChange={(e) => setOrderTp(e.target.value)}
              className="h-9 font-mono text-xs"
              disabled={!isRunning}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">SL (٪ ضرر)</Label>
            <Input
              value={orderSl}
              onChange={(e) => setOrderSl(e.target.value)}
              className="h-9 font-mono text-xs"
              disabled={!isRunning}
            />
          </div>
        </div>

        <Button
          onClick={onSubmit}
          disabled={
            !isRunning
            || isSubmitting
            || !parseNum(orderAmount)
            || openPositionsCount >= 10
          }
          className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700"
        >
          {isSubmitting
            ? "در حال ثبت..."
            : !isRunning
              ? "اول Paper را شروع کن"
              : variant === "guest"
                ? "ثبت خرید"
                : "ثبت سفارش"}
        </Button>

        {openPositionsCount >= 10 && (
          <p className="text-center text-[10px] text-amber-400">
            سقف ۱۰ پوزیشن باز پر است
          </p>
        )}
      </CardContent>
    </Card>
  );
}
