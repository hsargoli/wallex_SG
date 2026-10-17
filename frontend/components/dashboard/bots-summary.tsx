"use client";

import Link from "next/link";
import { Bot, ArrowUpRight, Play } from "lucide-react";
import { useBots, useUserPaperV3Status } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber } from "@/lib/format";

export function BotsSummary() {
  const bots = useBots();
  const paper = useUserPaperV3Status();

  const data = paper.data as Record<string, any> | undefined;
  const isRunning = data?.is_running ?? false;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-violet-400" />
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
      <CardContent className="space-y-3">
        <div className="rounded-lg border border-white/10 bg-white/5 p-3 flex items-center justify-between">
          <div>
            <p className="font-semibold text-sm">وضعیت Paper</p>
            <p className="text-xs text-muted-foreground">شبیه‌ساز فعال</p>
          </div>
          <Badge variant={isRunning ? "default" : "secondary"} className={isRunning ? "bg-emerald-600 hover:bg-emerald-500" : ""}>
            {isRunning ? "در حال اجرا" : "متوقف"}
          </Badge>
        </div>

        {bots.isLoading && <Skeleton className="h-10 w-full" />}
        
        {!bots.isLoading && bots.data?.bots?.slice(0, 2).map((b: any) => (
          <div key={b.slug} className="flex items-center justify-between text-sm py-1">
            <span className="text-muted-foreground">{b.name || b.slug}</span>
            <span className="font-mono text-xs">{b.status === 'running' ? 'فعال' : 'غیرفعال'}</span>
          </div>
        ))}

        {!isRunning && (
          <Button asChild variant="outline" size="sm" className="w-full mt-2 gap-2 border-violet-500/30 text-violet-300">
            <Link href="/guest">
              <Play className="h-3 w-3" />
              رفتن به تست زنده
            </Link>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
