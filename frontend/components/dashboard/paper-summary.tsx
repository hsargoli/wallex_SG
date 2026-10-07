"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Brain, Play } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

const num = (v: unknown, d = 2) =>
  typeof v === "number" && Number.isFinite(v)
    ? v.toLocaleString("en-US", { maximumFractionDigits: d })
    : "—";

const tone = (v: unknown) =>
  typeof v === "number" ? (v > 0 ? "text-emerald-500" : v < 0 ? "text-red-500" : "") : "";

export function PaperSummary() {
  const q = useQuery({
    queryKey: ["dash-paper-live"],
    queryFn: () => api.getPaperV3Live(),
    refetchInterval: 10_000,
    retry: 1,
  });

  if (q.isLoading) return null;

  const raw: any = q.data;
  const s: Record<string, any> = raw?.state ?? raw ?? {};
  const running = !!s.is_running;
  const never = !running && !(s.check_count > 0) && !(s.total_trades > 0);
  const events: any[] = Array.isArray(s.events) ? s.events : [];
  const radar: any[] = Array.isArray(s.radar) ? s.radar : [];
  const lastScan = events.find((e) => e.kind === "scan");
  const top = [...radar].sort((a, b) => (b.pct ?? 0) - (a.pct ?? 0))[0];
  const openCount = Array.isArray(s.open_positions) ? s.open_positions.length : 0;

  if (q.isError || never) {
    return (
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Brain className="h-5 w-5 text-violet-500" />
            {q.isError
              ? "اطلاعات تست زنده در دسترس نیست."
              : "هنوز تست زنده‌ای اجرا نشده. ربات را روی بازار واقعی و بدون پول واقعی امتحان کن."}
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

  const stats = [
    { l: "ارزش کل (USDT)", v: num(s.equity), c: "" },
    {
      l: "سود/زیان",
      v: (typeof s.total_pnl_pct === "number" && s.total_pnl_pct > 0 ? "+" : "") + num(s.total_pnl_pct) + "٪",
      c: tone(s.total_pnl_pct),
    },
    { l: "پوزیشن باز", v: String(openCount), c: "" },
    { l: "ترید بسته", v: `${s.total_trades ?? 0} · WR ${num(s.win_rate, 0)}٪`, c: "" },
  ];

  return (
    <Card className={running ? "border-emerald-500/30" : undefined}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-violet-500" />
            تست زنده (بدون پول واقعی)
            <Badge
              variant="outline"
              className={running ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"}
            >
              {running ? "در حال اجرا" : "متوقف"}
            </Badge>
          </span>
          <Link
            href="/paper-trading"
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            باز کردن <ArrowLeft className="h-3.5 w-3.5" />
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {stats.map((x) => (
            <div key={x.l}>
              <div className="text-xs text-muted-foreground">{x.l}</div>
              <div className={"mt-0.5 text-lg font-bold tabular-nums " + x.c} dir="ltr">
                {x.v}
              </div>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
          {lastScan && <span>آخرین اسکن: {lastScan.message}</span>}
          {top && top.total > 0 && (
            <span>
              نزدیک‌ترین کاندید: <span className="font-mono" dir="ltr">{top.symbol}</span>{" "}
              <span dir="ltr">{top.passed}/{top.total}</span> شرط
            </span>
          )}
          <span>{s.check_count ?? 0} چک انجام شده</span>
        </div>
      </CardContent>
    </Card>
  );
}
