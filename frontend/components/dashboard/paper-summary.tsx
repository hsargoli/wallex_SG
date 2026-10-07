"use client";

import Link from "next/link";
import { ArrowLeft, Brain, Play } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber, formatPct } from "@/lib/format";
import { usePaperLive } from "./use-paper-live";

export function PaperSummary() {
  const q = usePaperLive();
  if (q.isLoading) return <Skeleton className="h-28 w-full rounded-xl" />;

  const p = q.data;
  if (q.isError || !p || p.idle) {
    return (
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Brain className="h-5 w-5 text-violet-500" />
            {q.isError
              ? "اطلاعات تست زنده در دسترس نیست."
              : "تست زنده در حال اجرا نیست. ربات را روی بازار واقعی و بدون پول واقعی امتحان کن."}
          </div>
          <Link
            href="/paper-trading"
            className="flex items-center gap-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-600 hover:bg-emerald-500/20 dark:text-emerald-400"
          >
            <Play className="h-3.5 w-3.5" />
            رفتن به تست زنده
          </Link>
        </CardContent>
      </Card>
    );
  }

  const stats: { l: string; v: string; c?: string }[] = [
    { l: "ارزش کل", v: p.equity === null ? "—" : formatNumber(p.equity) },
    {
      l: "سود/زیان",
      v: p.pnlPct === null ? "—" : formatPct(p.pnlPct),
      c: p.pnlPct && p.pnlPct > 0 ? "text-emerald-500" : p.pnlPct && p.pnlPct < 0 ? "text-red-500" : "",
    },
    { l: "پوزیشن باز", v: String(p.openCount) },
  ];
  if (p.trades !== null) {
    stats.push({ l: "ترید بسته", v: p.winRate !== null ? `${p.trades} · WR ${formatNumber(p.winRate, { maximumFractionDigits: 0 })}%` : String(p.trades) });
  }

  return (
    <Card className={p.running ? "border-emerald-500/30" : undefined}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-violet-500" />
            تست زنده
            <Badge
              variant="outline"
              className={p.running ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"}
            >
              {p.running ? "در حال اجرا" : "متوقف"}
            </Badge>
          </span>
          <Link href="/paper-trading" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
            باز کردن <ArrowLeft className="h-3.5 w-3.5" />
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {stats.map((x) => (
            <div key={x.l}>
              <div className="text-xs text-muted-foreground">{x.l}</div>
              <div className={"mt-0.5 text-lg font-bold " + (x.c ?? "")}>
                <span dir="ltr" className="inline-block font-mono">{x.v}</span>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[10px] text-muted-foreground">بدون پول واقعی · بر پایه‌ی بازار زنده</p>
      </CardContent>
    </Card>
  );
}
