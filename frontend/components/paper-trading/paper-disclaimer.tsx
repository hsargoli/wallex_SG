/**
 * Paper Disclaimer — هشدار «شبیه‌سازی، نه ترید واقعی».
 * DRY ManualOrderForm — Phase 2.
 */
"use client";

import { ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type PaperDisclaimerProps = {
  variant?: "guest" | "user";
};

export function PaperDisclaimer({ variant = "user" }: PaperDisclaimerProps) {
  return (
    <Card className="border-amber-500/30 bg-amber-500/5 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-amber-300">
          <ShieldAlert className="h-4 w-4" />
          شبیه‌سازی، نه ترید واقعی
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
        <p>
          سفارش‌ها در{" "}
          <span className="font-bold text-amber-300">
            orderbook والکس نمی‌رن
          </span>
          . فقط در Paper state ذخیره می‌شوند.
        </p>
        <p>ترید واقعی تفاوت‌های مهمی دارد:</p>
        <ul className="mr-4 list-disc space-y-1">
          <li>نقدینگی واقعی (سفارش ممکنه fill نشه)</li>
          <li>Slippage (قیمت اجرا با قیمت درخواستی فرق می‌کنه)</li>
          <li>کارمزد صرافی</li>
          <li>تأخیر شبکه</li>
        </ul>
        <p className="pt-2 text-[10px] text-amber-300/70">
          {variant === "guest"
            ? "برای ترید واقعی، ثبت‌نام کن و توکن والکس بده."
            : "برای ترید واقعی، به /order-bot برو (نیاز به توکن والکس)."}
        </p>
      </CardContent>
    </Card>
  );
}
