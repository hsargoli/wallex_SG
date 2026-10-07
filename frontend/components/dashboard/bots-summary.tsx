"use client";

import Link from "next/link";
import { Bot, ArrowUpRight, FlaskConical, Play } from "lucide-react";
import { useBots } from "@/lib/queries";
import { SUPPORT, NON_TRADING, botScore } from "@/lib/bot-support";
import { usePaperLive } from "./use-paper-live";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function Chip({ icon: Icon, label, on }: { icon: React.ElementType; label: string; on: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px]",
        on
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
          : "border-zinc-500/20 text-muted-foreground/60",
      )}
    >
      <Icon className="h-2.5 w-2.5" />
      {label}
      {!on && <span className="opacity-70">· به‌زودی</span>}
    </span>
  );
}

export function BotsSummary() {
  const bots = useBots();
  const paper = usePaperLive();
  const paperRunning = paper.data?.running === true;

  const list = [...(bots.data?.bots ?? [])]
    .filter((b) => !NON_TRADING.has(b.slug))
    .sort((a, b) => botScore(b.slug) - botScore(a.slug))
    .slice(0, 4);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-blue-400" />
            ربات‌ها
          </span>
          <Link href="/bots">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              مشاهده همه
              <ArrowUpRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0.5">
        {bots.isLoading && (
          <>
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </>
        )}
        {list.map((b) => {
          const sup = SUPPORT[b.slug] ?? { backtest: false, paper: false };
          const live = sup.paper && paperRunning;
          return (
            <Link
              key={b.slug}
              href={`/bots/${b.slug}`}
              className="group flex items-center gap-3 rounded-lg border border-transparent px-3 py-2.5 transition-all hover:border-border hover:bg-white/[0.02]"
            >
              <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", live ? "bg-emerald-500/15 text-emerald-400" : "bg-white/5 text-muted-foreground")}>
                <Bot className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium">{b.name}</p>
                  {live && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />}
                </div>
                <p className="truncate text-[10px] text-muted-foreground">{b.name_en}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <Chip icon={FlaskConical} label="بک‌تست" on={sup.backtest} />
                <Chip icon={Play} label="تست زنده" on={sup.paper} />
              </div>
            </Link>
          );
        })}
        {!bots.isLoading && list.length === 0 && (
          <p className="py-8 text-center text-xs text-muted-foreground">رباتی ثبت نشده</p>
        )}
      </CardContent>
    </Card>
  );
}
