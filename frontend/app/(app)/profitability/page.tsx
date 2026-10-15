"use client";

import { useState } from "react";
import {
  Calculator,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { useMarkets, useProfitability } from "@/lib/queries";
import { formatNumber, formatPct, formatPrice } from "@/lib/format";
import { type OrderType } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { Badge } from "@/components/ui/badge";

export default function ProfitabilityPage() {
  const markets = useMarkets();
  const mutation = useProfitability();

  const [symbol, setSymbol] = useState("XRPTMN");
  const [orderType, setOrderType] = useState<OrderType>("maker");
  const [capital, setCapital] = useState("1000000");
  const [slippage, setSlippage] = useState("0");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      symbol,
      order_type: orderType,
      capital: Number(capital),
      slippage_pct: Number(slippage),
    });
  };

  const result = mutation.data;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">محاسبه‌گر سودآوری</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          بررسی می‌کند که آیا با شرایط فعلی بازار و کارمزد، معامله سودآور است
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-emerald-400" />
              پارامترها
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>نماد</Label>
                <Select value={symbol} onValueChange={setSymbol}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {markets.data?.items.slice(0, 30).map((m) => (
                      <SelectItem key={m.symbol} value={m.symbol}>
                        <span className="font-mono">{m.symbol}</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>نوع سفارش</Label>
                <div className="grid grid-cols-2 gap-2">
                  {(["maker", "taker"] as OrderType[]).map((t) => (
                    <Button
                      key={t}
                      type="button"
                      variant={orderType === t ? "default" : "outline"}
                      onClick={() => setOrderType(t)}
                      className={
                        orderType === t ? "bg-emerald-600 hover:bg-emerald-700" : ""
                      }
                    >
                      {t === "maker" ? "Maker" : "Taker"}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="capital">سرمایه (TMN)</Label>
                <Input
                  id="capital"
                  type="number"
                  step="any"
                  min="1"
                  value={capital}
                  onChange={(e) => setCapital(e.target.value)}
                  className="font-mono"
                />
              </div>

              {orderType === "taker" && (
                <div className="space-y-2">
                  <Label htmlFor="slippage">لغزش قیمت (٪)</Label>
                  <Input
                    id="slippage"
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={slippage}
                    onChange={(e) => setSlippage(e.target.value)}
                    className="font-mono"
                  />
                </div>
              )}

              <Button
                type="submit"
                disabled={mutation.isPending}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                {mutation.isPending ? "در حال محاسبه..." : "محاسبه"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="lg:col-span-3 space-y-4">
          {!result ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-20 text-center">
                <Calculator className="mb-4 h-12 w-12 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">
                  پارامترها را وارد کنید و «محاسبه» را بزنید
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <Card
                className={`border-2 ${
                  result.is_profitable
                    ? "border-emerald-500/30 bg-emerald-500/5"
                    : "border-red-500/30 bg-red-500/5"
                }`}
              >
                <CardContent className="flex items-center gap-4 py-6">
                  {result.is_profitable ? (
                    <CheckCircle2 className="h-10 w-10 text-emerald-400" />
                  ) : (
                    <AlertCircle className="h-10 w-10 text-red-400" />
                  )}
                  <div className="flex-1">
                    <p className="text-lg font-bold">
                      {result.is_profitable
                        ? "معامله سودآور است"
                        : "معامله سودآور نیست"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {result.notes[0] ?? "بر اساس پارامترهای ورودی"}
                    </p>
                  </div>
                  <Badge variant="outline">{result.order_type}</Badge>
                </CardContent>
              </Card>

              <div className="grid gap-4 sm:grid-cols-2">
                <StatBox
                  label="سود/زیان خالص"
                  value={`${formatNumber(result.net_profit)} TMN`}
                  accent={
                    Number(result.net_profit) >= 0
                      ? "text-emerald-400"
                      : "text-red-400"
                  }
                  icon={
                    Number(result.net_profit) >= 0 ? TrendingUp : TrendingDown
                  }
                />
                <StatBox
                  label="درصد سود"
                  value={formatPct(result.net_profit_pct)}
                  accent={
                    Number(result.net_profit_pct) >= 0
                      ? "text-emerald-400"
                      : "text-red-400"
                  }
                />
                <StatBox
                  label="اسپرد بازار"
                  value={`${formatPrice(result.spread)} (${Number(
                    result.spread_pct,
                  ).toFixed(4)}%)`}
                  accent="text-amber-400"
                />
                <StatBox
                  label="حداقل اسپرد لازم"
                  value={formatPrice(result.min_profitable_spread)}
                  accent="text-purple-400"
                />
                <StatBox
                  label="کارمزد خرید"
                  value={`${formatNumber(result.buy_fee)} TMN`}
                  accent="text-red-400"
                />
                <StatBox
                  label="کارمزد فروش"
                  value={`${formatNumber(result.sell_fee)} TMN`}
                  accent="text-red-400"
                />
                <StatBox
                  label="سود ناخالص"
                  value={`${formatNumber(result.gross_profit)} TMN`}
                  accent="text-emerald-400"
                />
                <StatBox
                  label="نرخ کارمزد"
                  value={`${(Number(result.applied_fee_rate) * 100).toFixed(4)}%`}
                  accent="text-blue-400"
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function StatBox({
  label,
  value,
  accent,
  icon: Icon,
}: {
  label: string;
  value: string;
  accent: string;
  icon?: React.ElementType;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <div className="mt-1 flex items-center gap-2">
        {Icon && <Icon className={`h-4 w-4 ${accent}`} />}
        <p className={`font-mono text-lg font-bold ${accent}`}>{value}</p>
      </div>
    </div>
  );
}
