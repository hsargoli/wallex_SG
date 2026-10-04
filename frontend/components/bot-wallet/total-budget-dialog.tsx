"use client";

import { useEffect, useState } from "react";
import { Save, Loader2, Wallet, Info } from "lucide-react";
import { useTotalBudget, useSetBudget } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

const PRESETS = [100_000, 500_000, 1_000_000, 5_000_000];

export function TotalBudgetDialog() {
  const [open, setOpen] = useState(false);
  const total = useTotalBudget();
  const setBudget = useSetBudget();
  const [value, setValue] = useState("");

  useEffect(() => {
    if (total.data) setValue(total.data.total_budget);
  }, [total.data]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount <= 0) return;
    setBudget.mutate(amount, {
      onSuccess: () => setOpen(false),
    });
  };

  const currentTotal = Number(total.data?.total_budget || 0);
  const allocated = Number(total.data?.total_allocated || 0);
  const entered = Number(value || 0);
  const validAmount = entered >= allocated;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
          <Wallet className="h-4 w-4" />
          تنظیم بودجه‌ی کل
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-emerald-400" />
            تنظیم بودجه‌ی کل
          </DialogTitle>
          <DialogDescription>
            سقف کلی سرمایه‌ای که ربات‌ها می‌توانند استفاده کنند
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="total-budget">بودجه‌ی کل (TMN)</Label>
            <Input
              id="total-budget"
              type="number"
              step="any"
              min="0"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="مثلاً 1000000"
              className="font-mono text-lg"
              autoFocus
            />
            {value && entered > 0 && (
              <p className="text-xs text-muted-foreground">
                معادل {formatNumber(value)} تومان
              </p>
            )}
          </div>

          {/* Presets */}
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((preset) => (
              <Button
                key={preset}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setValue(String(preset))}
                className="font-mono text-xs"
              >
                {formatNumber(preset)}
              </Button>
            ))}
          </div>

          {/* Validation warning */}
          {value && entered < allocated && (
            <Alert className="bg-red-500/10 border-red-500/30">
              <AlertDescription className="text-xs text-red-400 leading-relaxed">
                بودجه‌ی کل نمی‌تواند کمتر از مجموع تخصیص‌ها (
                {formatNumber(allocated)} TMN) باشد. ابتدا تخصیص ربات‌ها را
                کاهش دهید.
              </AlertDescription>
            </Alert>
          )}

          {/* Info */}
          {(!value || entered >= allocated) && (
            <Alert className="bg-blue-500/5 border-blue-500/20">
              <Info className="h-4 w-4 text-blue-400" />
              <AlertDescription className="text-xs text-blue-200/80 leading-relaxed">
                بودجه را فقط زمانی کاهش دهید که سفارش باز ندارید. سیستم اجازه
                نمی‌دهد بودجه از سرمایه‌ی درگردش کمتر شود.
              </AlertDescription>
            </Alert>
          )}

          {/* Actions */}
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
              disabled={setBudget.isPending || !validAmount}
              className="flex-1 gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              {setBudget.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  ذخیره
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
