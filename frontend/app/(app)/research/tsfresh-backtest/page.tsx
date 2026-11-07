"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertTriangle, TrendingDown, BarChart3, XCircle, Info, ArrowLeft,
} from "lucide-react";

interface VerdictTest {
  id: string;
  direction_code: "long" | "short" | "long-red";
  direction_fa: string;
  n_matches: number;
  horizon_h: number;
  trades: number;
  win_rate_pct: number;
  profit_factor: number;
  max_dd_pct: number;
  verdict: "fail";
}

interface VerdictData {
  as_of: string;
  adr: string;
  verdict: "no_edge";
  verdict_label_fa: string;
  verdict_desc_fa: string;
  params: {
    TP_pct: number;
    SL_pct: number;
    Fee_pct: number;
    break_even_wr_pct: number;
    random_walk_wr_pct: number;
  };
  key_insight_fa: string;
  tests: VerdictTest[];
  rejected_hypotheses_fa: string[];
}

export default function TSFreshBacktestVerdictPage() {
  const [data, setData] = useState<VerdictData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/tsfresh-verdict.json")
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="container py-8">
        <Card className="border-rose-500/30">
          <CardHeader>
            <CardTitle className="text-rose-400 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" /> خطا در بارگذاری داده
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container py-8 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const maxY = Math.max(data.params.break_even_wr_pct * 1.15, 50);
  const breakEvenBottomPct = (data.params.break_even_wr_pct / maxY) * 100;

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" /> نتیجه بک‌تست tsfresh
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            تحلیل ۶ تست پیش‌ثبت‌شده — طبق {data.adr}
          </p>
        </div>
        <Badge variant="outline" className="text-xs">Research · Verdict only</Badge>
      </div>

      {/* Verdict banner */}
      <Card className="border-rose-500/40 bg-rose-500/5">
        <CardContent className="pt-6 pb-6 text-center space-y-3">
          <Badge variant="outline" className="border-rose-500/60 text-rose-300 text-base px-4 py-1">
            <XCircle className="h-4 w-4 mr-1" /> NO EDGE CONFIRMED
          </Badge>
          <h2 className="text-2xl font-bold text-rose-400">{data.verdict_label_fa}</h2>
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            {data.verdict_desc_fa}
          </p>
        </CardContent>
      </Card>

      {/* Key Insight */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Info className="h-4 w-4 text-amber-400" /> چرا این نتیجه قطعی است؟
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-foreground/90">
            {data.key_insight_fa}
          </p>
          <div className="grid grid-cols-3 gap-3 mt-4 text-xs">
            <div className="border rounded-lg p-2 bg-background/50">
              <div className="text-muted-foreground">random walk</div>
              <div className="font-mono text-base text-slate-300">
                {data.params.random_walk_wr_pct}٪
              </div>
            </div>
            <div className="border rounded-lg p-2 bg-background/50">
              <div className="text-muted-foreground">break-even</div>
              <div className="font-mono text-base text-rose-400">
                {data.params.break_even_wr_pct}٪
              </div>
            </div>
            <div className="border rounded-lg p-2 bg-background/50">
              <div className="text-muted-foreground">میانگین مشاهده</div>
              <div className="font-mono text-base text-amber-400">~33٪</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tests table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4" /> ۶ تست پیش‌ثبت‌شده
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border border-border/50">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 text-xs text-muted-foreground">
                <tr>
                  <th className="text-right py-2 px-3 font-normal">#</th>
                  <th className="text-right py-2 px-3 font-normal">جهت</th>
                  <th className="text-right py-2 px-3 font-normal">N</th>
                  <th className="text-right py-2 px-3 font-normal">افق</th>
                  <th className="text-right py-2 px-3 font-normal">Trades</th>
                  <th className="text-right py-2 px-3 font-normal">WR</th>
                  <th className="text-right py-2 px-3 font-normal">PF</th>
                  <th className="text-right py-2 px-3 font-normal">MaxDD</th>
                  <th className="text-right py-2 px-3 font-normal">Verdict</th>
                </tr>
              </thead>
              <tbody>
                {data.tests.map((t) => (
                  <tr key={t.id} className="border-t border-border/30 hover:bg-muted/20 transition-colors">
                    <td className="py-2 px-3 text-right font-mono text-xs">{t.id}</td>
                    <td className="py-2 px-3 text-right text-xs">{t.direction_fa}</td>
                    <td className="py-2 px-3 text-right font-mono text-xs">{t.n_matches}</td>
                    <td className="py-2 px-3 text-right font-mono text-xs">{t.horizon_h}h</td>
                    <td className="py-2 px-3 text-right font-mono text-xs">{t.trades.toLocaleString()}</td>
                    <td className={`py-2 px-3 text-right font-mono text-xs ${t.win_rate_pct >= data.params.break_even_wr_pct ? "text-emerald-400" : "text-rose-400"}`}>
                      {t.win_rate_pct}%
                    </td>
                    <td className={`py-2 px-3 text-right font-mono text-xs ${t.profit_factor >= 1 ? "text-emerald-400" : "text-rose-400"}`}>
                      {t.profit_factor.toFixed(2)}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-xs text-rose-400">
                      {t.max_dd_pct}%
                    </td>
                    <td className="py-2 px-3 text-right">
                      <Badge variant="outline" className="border-rose-500/40 text-rose-300 text-xs">
                        FAIL
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            آستانه‌ی موفقیت (AP-57): PF &gt; 1.2 + WR &gt; break-even + N ≥ 30 + MaxDD &gt; −20٪. هیچ تستی از این آستانه عبور نکرد.
          </p>
        </CardContent>
      </Card>

      {/* WR vs break-even visual */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingDown className="h-4 w-4" /> Win Rate هر تست در برابر break-even
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative h-56 border-l border-b border-border/50">
            <div
              className="absolute left-0 right-0 border-t border-dashed border-rose-500/60"
              style={{ bottom: `${breakEvenBottomPct}%` }}
            >
              <span className="absolute -top-4 right-0 text-xs text-rose-400 font-mono bg-background px-1">
                break-even: {data.params.break_even_wr_pct}٪
              </span>
            </div>
            <div className="absolute inset-0 flex items-end justify-around px-2">
              {data.tests.map((t) => (
                <div
                  key={t.id}
                  className="w-[12%] bg-rose-500/60 rounded-t hover:bg-rose-500/80 transition-colors"
                  style={{ height: `${(t.win_rate_pct / maxY) * 100}%` }}
                  title={`${t.id}: ${t.win_rate_pct}%`}
                />
              ))}
            </div>
          </div>
          <div className="flex justify-around px-2 mt-2">
            {data.tests.map((t) => (
              <div key={t.id} className="w-[12%] text-center">
                <div className="text-xs font-mono text-rose-400">{t.win_rate_pct}%</div>
                <div className="text-xs text-muted-foreground">{t.id}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-3 text-center">
            همه‌ی تست‌ها زیر خط break-even — ۱۱ تا ۱۸ واحد فاصله.
          </p>
        </CardContent>
      </Card>

      {/* Rejected hypotheses */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <XCircle className="h-4 w-4 text-rose-400" /> فرضیه‌های رد شده
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {data.rejected_hypotheses_fa.map((h, i) => (
              <li key={i} className="flex items-start gap-2">
                <XCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="text-muted-foreground">{h}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2 text-xs text-amber-200/90">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <strong>هشدار:</strong> این نتیجه صرفاً برای مستندسازی است. هیچ‌کدام از این ۶ استراتژی نباید در Live یا Paper به‌عنوان «سیگنال» استفاده شوند. طبق ADR-0034 (Copilot نه Autopilot)، Nooaah تنها ربات فعال است و به HumanSignal (ADR-0037) و SarvRouter gate وابسته است.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-xs text-muted-foreground text-center pt-2 space-y-1">
        <p>
          as_of: <span className="font-mono">{data.as_of}</span> · منبع:{" "}
          <span className="font-mono">{data.adr}</span>
        </p>
        <Link
          href="/research/tsfresh"
          className="inline-flex items-center gap-1 mt-2 text-primary hover:underline"
        >
          <ArrowLeft className="h-3 w-3 rotate-180" /> مشاهده تحلیل تشابه تاریخی
        </Link>
      </div>
    </div>
  );
}
