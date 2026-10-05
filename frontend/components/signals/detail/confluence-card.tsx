"use client";

import { TrendingUp, TrendingDown, AlertCircle, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { InfoTip } from "@/components/ui/info-tip";
import { cn } from "@/lib/utils";

interface ConfluenceData {
  status: string;
  label: string;
  buy_count: number;
  sell_count: number;
  hold_count: number;
}

interface ConfluenceCardProps {
  data?: ConfluenceData;
  loading?: boolean;
}

export function ConfluenceCard({ data, loading }: ConfluenceCardProps) {
  if (loading) return <Skeleton className="h-24 w-full" />;
  if (!data) return null;

  const config =
    {
      strong_buy: {
        color: "text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/30",
        icon: TrendingUp,
      },
      lean_buy: {
        color: "text-emerald-300",
        bg: "bg-emerald-500/5 border-emerald-500/20",
        icon: TrendingUp,
      },
      strong_sell: {
        color: "text-red-400",
        bg: "bg-red-500/10 border-red-500/30",
        icon: TrendingDown,
      },
      lean_sell: {
        color: "text-red-300",
        bg: "bg-red-500/5 border-red-500/20",
        icon: TrendingDown,
      },
      mixed: {
        color: "text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/30",
        icon: AlertCircle,
      },
      neutral: {
        color: "text-zinc-400",
        bg: "bg-white/5 border-white/10",
        icon: Minus,
      },
    }[data.status] ?? {
      color: "text-zinc-400",
      bg: "bg-white/5 border-white/10",
      icon: Minus,
    };

  const Icon = config.icon;

  return (
    <Card className={cn("border", config.bg)}>
      <CardContent className="flex flex-wrap items-center justify-between gap-4 py-5">
        <div className="flex items-center gap-4">
          <Icon className={cn("h-10 w-10", config.color)} />
          <div>
            <p className="flex items-center gap-1 text-xs text-muted-foreground">
              تأیید متقابل تایم‌فریم
              <InfoTip text="اگه سیگنال در چند تایم‌فریم (15m، 1h، 4h، 1D) هم‌جهت باشه، اطمینان بالاتر می‌ره. مثلاً ۴ از ۴ خرید = سیگنال خیلی قوی." />
            </p>
            <p className={cn("text-lg font-bold", config.color)}>{data.label}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="border-emerald-500/30 text-emerald-400"
          >
            🟢 {data.buy_count} خرید
          </Badge>
          <Badge variant="outline" className="border-red-500/30 text-red-400">
            🔴 {data.sell_count} فروش
          </Badge>
          <Badge variant="outline" className="border-zinc-500/30 text-zinc-400">
            ⚪ {data.hold_count} صبر
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
