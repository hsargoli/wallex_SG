"use client";

import { Wallet, TrendingUp, Activity, Percent } from "lucide-react";
import { useBudget, useMarkets } from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

function StatCard({
  title,
  value,
  hint,
  icon: Icon,
  accent = "emerald",
  loading,
}: {
  title: string;
  value: string;
  hint?: string;
  icon: React.ElementType;
  accent?: "emerald" | "blue" | "purple" | "amber";
  loading?: boolean;
}) {
  const accents = {
    emerald: "from-emerald-500/20 to-emerald-500/0 text-emerald-400",
    blue: "from-blue-500/20 to-blue-500/0 text-blue-400",
    purple: "from-purple-500/20 to-purple-500/0 text-purple-400",
    amber: "from-amber-500/20 to-amber-500/0 text-amber-400",
  };
  const accentIcon = accents[accent].split(" ").pop();

  return (
    <Card className="relative overflow-hidden">
      <div
        className={`pointer-events-none absolute -left-16 -top-16 h-40 w-40 rounded-full bg-gradient-to-br ${accents[accent]} blur-2xl`}
      />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className={`h-4 w-4 ${accentIcon}`} />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-32" />
        ) : (
          <div className="text-2xl font-bold tracking-tight">{value}</div>
        )}
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const budget = useBudget();
  const markets = useMarkets();

  const allocated = budget.data?.allocated_budget ?? "0";
  const inUse = budget.data?.in_use_capital ?? "0";
  const available = budget.data?.available_for_trade ?? "0";
  const usagePct =
    Number(allocated) > 0 ? (Number(inUse) / Number(allocated)) * 100 : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">داشبورد</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          نمای کلی از وضعیت ربات و بازار
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="بودجه کل"
          value={`${formatNumber(allocated)} TMN`}
          hint="سرمایه تخصیص‌یافته به ربات"
          icon={Wallet}
          accent="emerald"
          loading={budget.isLoading}
        />
        <StatCard
          title="سرمایه در گردش"
          value={`${formatNumber(inUse)} TMN`}
          hint={`${usagePct.toFixed(1)}% از بودجه`}
          icon={Activity}
          accent="amber"
          loading={budget.isLoading}
        />
        <StatCard
          title="موجود برای معامله"
          value={`${formatNumber(available)} TMN`}
          hint="آماده برای معامله بعدی"
          icon={TrendingUp}
          accent="blue"
          loading={budget.isLoading}
        />
        <StatCard
          title="نرخ استفاده"
          value={`${usagePct.toFixed(1)}%`}
          hint="درصد سرمایه درگیر"
          icon={Percent}
          accent="purple"
          loading={budget.isLoading}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>بازارهای فعال</CardTitle>
          <CardDescription>
            {markets.data
              ? `${markets.data.count} نماد در دسترس`
              : "در حال بارگذاری..."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {markets.isLoading ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {markets.data?.items.slice(0, 9).map((m) => (
                <div
                  key={m.symbol}
                  className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 transition hover:border-emerald-500/20 hover:bg-emerald-500/5"
                >
                  <div>
                    <p className="text-sm font-semibold">{m.symbol}</p>
                    <p className="text-xs text-muted-foreground">
                      {m.fa_name ?? m.en_name ?? "—"}
                    </p>
                  </div>
                  <Badge
                    variant="outline"
                    className="border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                  >
                    فعال
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
