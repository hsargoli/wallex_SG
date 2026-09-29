"use client";

import { useEffect, useState } from "react";
import { Wallet, Save, Info } from "lucide-react";
import { useBudget, useSetBudget } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

export default function BudgetPage() {
  const budget = useBudget();
  const setBudget = useSetBudget();
  const [value, setValue] = useState<string>("");

  useEffect(() => {
    if (budget.data) setValue(budget.data.allocated_budget);
  }, [budget.data]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount <= 0) return;
    setBudget.mutate(amount);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">مدیریت بودجه</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          سقف سرمایه‌ای که ربات می‌تواند در معاملات استفاده کند
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-5 w-5 text-emerald-400" />
              تعیین بودجه
            </CardTitle>
            <CardDescription>مقدار بودجه را به واحد TMN وارد کنید</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="budget">بودجه کل (TMN)</Label>
                <Input
                  id="budget"
                  type="number"
                  step="any"
                  min="1"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder="مثلاً 1000000"
                  className="font-mono text-lg"
                />
                {value && Number(value) > 0 && (
                  <p className="text-xs text-muted-foreground">
                    معادل {formatNumber(value)} تومان
                  </p>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                {[100000, 500000, 1000000, 5000000].map((preset) => (
                  <Button
                    key={preset}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setValue(String(preset))}
                  >
                    {formatNumber(preset)}
                  </Button>
                ))}
              </div>

              <Button
                type="submit"
                disabled={setBudget.isPending}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                <Save className="ml-2 h-4 w-4" />
                {setBudget.isPending ? "در حال ذخیره..." : "ذخیره بودجه"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">وضعیت فعلی</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {budget.isLoading ? (
              <>
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </>
            ) : (
              <>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">بودجه کل</p>
                  <p className="font-mono text-lg font-semibold">
                    {formatNumber(budget.data?.allocated_budget ?? 0)} TMN
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">در گردش</p>
                  <p className="font-mono text-lg font-semibold text-amber-400">
                    {formatNumber(budget.data?.in_use_capital ?? 0)} TMN
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">
                    آزاد برای معامله
                  </p>
                  <p className="font-mono text-lg font-semibold text-emerald-400">
                    {formatNumber(budget.data?.available_for_trade ?? 0)} TMN
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-amber-500/20 bg-amber-500/5">
        <CardContent className="flex items-start gap-3 py-4">
          <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" />
          <div className="text-sm">
            <p className="font-medium text-amber-200">نکته امنیتی</p>
            <p className="text-xs text-amber-200/80">
              بودجه را فقط زمانی کاهش دهید که سفارش باز ندارید. سیستم اجازه
              نمی‌دهد بودجه از سرمایه‌ی درگیر کمتر شود.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
