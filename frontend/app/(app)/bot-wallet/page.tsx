"use client";

import { Bot, Wallet, Info } from "lucide-react";
import { useBots } from "@/lib/queries";
import { TotalBudgetCard } from "@/components/bot-wallet/total-budget-card";
import { TotalBudgetDialog } from "@/components/bot-wallet/total-budget-dialog";
import { BotAllocationCard } from "@/components/bot-wallet/bot-allocation-card";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function BotWalletPage() {
  const bots = useBots();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/30 to-emerald-500/0">
          <Wallet className="h-6 w-6 text-emerald-400" />
        </div>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">کیف پول ربات</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            مدیریت بودجه و تخصیص سرمایه به ربات‌های معاملاتی
          </p>
        </div>
        <TotalBudgetDialog />
      </div>

      {/* Info */}
      <Alert className="bg-blue-500/5 border-blue-500/20">
        <Info className="h-4 w-4 text-blue-400" />
        <AlertDescription className="text-xs text-blue-200/80 leading-relaxed">
          هر ربات فقط با بودجه‌ی اختصاصی خودش می‌تواند معامله کند. مجموع
          تخصیص‌ها از بودجه‌ی کل قابل افزایش نیست.
        </AlertDescription>
      </Alert>

      {/* Total budget cards */}
      <TotalBudgetCard />

      {/* Bots allocations */}
      <div>
        <div className="mb-4 flex items-center gap-2">
          <Bot className="h-5 w-5 text-emerald-400" />
          <h2 className="text-lg font-bold">تخصیص به ربات‌ها</h2>
          {bots.data && (
            <span className="text-xs text-muted-foreground">
              ({bots.data.count} ربات)
            </span>
          )}
        </div>

        {bots.isLoading && (
          <div className="grid gap-4 lg:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-48 w-full" />
            ))}
          </div>
        )}

        {bots.data?.bots && bots.data.bots.length > 0 && (
          <div className="grid gap-4 lg:grid-cols-2">
            {bots.data.bots.map((bot) => (
              <BotAllocationCard key={bot.slug} bot={bot} />
            ))}
          </div>
        )}

        {!bots.isLoading && (!bots.data?.bots || bots.data.bots.length === 0) && (
          <Card>
            <CardContent className="py-16 text-center">
              <Bot className="mx-auto mb-3 h-10 w-10 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">
                رباتی ثبت نشده
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
