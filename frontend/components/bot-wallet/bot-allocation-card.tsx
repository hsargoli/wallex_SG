"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Bot,
  Edit3,
  Check,
  X,
  TrendingUp,
  TrendingDown,
  Play,
  Square,
  ArrowUpRight,
  Loader2,
} from "lucide-react";
import {
  useBotBudget,
  useBotStatus,
  useSetBotBudget,
} from "@/lib/queries";
import { formatNumber } from "@/lib/format";
import type { BotInfo } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface BotAllocationCardProps {
  bot: BotInfo;
}

export function BotAllocationCard({ bot }: BotAllocationCardProps) {
  const budget = useBotBudget(bot.slug);
  const status = useBotStatus(bot.slug);
  const setBudget = useSetBotBudget();

  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");

  useEffect(() => {
    if (budget.data) {
      setValue(budget.data.allocated);
    }
  }, [budget.data]);

  const handleSave = () => {
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount < 0) return;
    setBudget.mutate(
      { slug: bot.slug, amount },
      {
        onSuccess: () => setEditing(false),
      },
    );
  };

  const handleCancel = () => {
    setValue(budget.data?.allocated || "0");
    setEditing(false);
  };

  const isRunning = status.data?.is_running ?? false;
  const pnl = status.data?.total_return_pct ?? 0;
  const isPositive = pnl >= 0;
  const profitTmn = status.data?.profit_tmn ?? 0;

  const allocated = Number(budget.data?.allocated || 0);
  const inUse = Number(budget.data?.in_use || 0);
  const free = Number(budget.data?.free || 0);
  const usagePct = budget.data?.usage_pct ?? 0;

  return (
    <Card
      className={cn(
        "overflow-hidden transition-all",
        isRunning && "border-emerald-500/30",
      )}
    >
      <CardContent className="pt-5">
        {/* Header row */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          {/* Icon */}
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
              isRunning
                ? "bg-emerald-500/15 text-emerald-400"
                : "bg-white/5 text-muted-foreground",
            )}
          >
            <Bot className="h-5 w-5" />
          </div>

          {/* Name */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Link
                href={`/bots/${bot.slug}`}
                className="truncate text-sm font-bold hover:text-emerald-400"
              >
                {bot.name}
              </Link>
              {isRunning ? (
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              ) : (
                <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
              )}
            </div>
            <p className="truncate text-[10px] text-muted-foreground">
              {bot.name_en}
            </p>
          </div>

          {/* Status badge */}
          <Badge
            variant="outline"
            className={cn(
              "gap-1 text-[10px]",
              isRunning
                ? "border-emerald-500/30 bg-emerald-500/15 text-emerald-400"
                : "border-zinc-500/30 bg-zinc-500/10 text-zinc-400",
            )}
          >
            {isRunning ? (
              <>
                <Play className="h-2.5 w-2.5" />
                فعال
              </>
            ) : (
              <>
                <Square className="h-2.5 w-2.5" />
                غیرفعال
              </>
            )}
          </Badge>
        </div>

        {/* Budget row */}
        <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          {/* Left: inputs/values */}
          <div>
            <p className="mb-1.5 text-[10px] text-muted-foreground">
              بودجه‌ی اختصاصی (TMN)
            </p>
            {editing ? (
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  className="h-9 font-mono text-sm"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSave();
                    if (e.key === "Escape") handleCancel();
                  }}
                />
                <Button
                  size="icon"
                  onClick={handleSave}
                  disabled={setBudget.isPending}
                  className="h-9 w-9 bg-emerald-600 hover:bg-emerald-700"
                >
                  {setBudget.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Check className="h-3.5 w-3.5" />
                  )}
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  onClick={handleCancel}
                  disabled={setBudget.isPending}
                  className="h-9 w-9"
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <p className="font-mono text-lg font-bold text-emerald-400">
                  {formatNumber(allocated)}
                </p>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => setEditing(true)}
                  className="h-7 w-7"
                  title="ویرایش بودجه"
                >
                  <Edit3 className="h-3.5 w-3.5" />
                </Button>
              </div>
            )}
          </div>

          {/* Right: usage % */}
          {!editing && allocated > 0 && (
            <div className="flex items-center gap-3 text-left sm:flex-col sm:items-end sm:gap-1">
              <div>
                <p className="text-[10px] text-muted-foreground">در گردش</p>
                <p className="font-mono text-sm font-bold">
                  {formatNumber(inUse)}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">آزاد</p>
                <p className="font-mono text-sm">{formatNumber(free)}</p>
              </div>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {!editing && allocated > 0 && (
          <div className="mt-3">
            <div className="mb-1 flex items-center justify-between text-[10px] text-muted-foreground">
              <span>استفاده</span>
              <span className="font-mono">{usagePct.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  usagePct > 80
                    ? "bg-red-500"
                    : usagePct > 50
                      ? "bg-amber-500"
                      : "bg-emerald-500",
                )}
                style={{ width: `${Math.min(usagePct, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* PnL footer */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border/50 pt-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">سود/زیان:</span>
            <span
              className={cn(
                "flex items-center gap-1 font-mono font-bold",
                isPositive ? "text-emerald-400" : "text-red-400",
              )}
            >
              {isPositive ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {isPositive ? "+" : ""}
              {pnl.toFixed(2)}%
            </span>
            <span
              className={cn(
                "font-mono text-[10px]",
                isPositive ? "text-emerald-400/70" : "text-red-400/70",
              )}
            >
              ({isPositive ? "+" : ""}
              {formatNumber(profitTmn)} TMN)
            </span>
          </div>

          <Link href={`/bots/${bot.slug}`}>
            <Button variant="ghost" size="sm" className="h-7 gap-1 text-[10px]">
              جزئیات
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
