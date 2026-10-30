"use client";

import Link from "next/link";
import { Wallet, Sparkles, ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatNumber } from "@/lib/format";
import { useMe } from "@/lib/queries";
import { hasUserToken } from "@/lib/auth";

const GUEST_CAPITAL = 100_000;
const USER_CAPITAL = 10_000_000;

export function CapitalCard() {
  const isUser = hasUserToken();
  const me = useMe();

  // Fallback: اگر useMe هنوز بارگذاری نشده، از مقدار پیش‌فرض استفاده کن
  const capital = isUser
    ? (me.data?.capital_total ?? USER_CAPITAL)
    : GUEST_CAPITAL;

  return (
    <Card className={isUser ? "border-emerald-500/30 bg-emerald-500/5" : "border-amber-500/30 bg-amber-500/5"}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            سرمایه Paper
          </span>
          <Badge variant="outline" className={isUser ? "border-emerald-500/40 text-emerald-400" : "border-amber-500/40 text-amber-400"}>
            {isUser ? "کاربر" : "مهمان"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline gap-2">
          <p className="text-2xl font-bold">{formatNumber(capital)}</p>
          <p className="text-xs text-muted-foreground">تومان</p>
        </div>

        {isUser ? (
          <p className="text-xs text-muted-foreground">
            سرمایه‌ی Paper شما. برای Live، پس از ۳۰ روز Paper موفق فعال می‌شود.
          </p>
        ) : (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground flex items-start gap-1">
              <Sparkles className="h-3 w-3 mt-0.5 text-amber-400 shrink-0" />
              <span>۱۰۰ هزار تومان رایگان. با ثبت‌نام، ۱۰ میلیون تومان.</span>
            </p>
            <Link href="/register">
              <Button size="sm" className="w-full gap-1 bg-amber-600 hover:bg-amber-700">
                ثبت‌نام (۱۰M)
                <ArrowLeft className="h-3 w-3" />
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
