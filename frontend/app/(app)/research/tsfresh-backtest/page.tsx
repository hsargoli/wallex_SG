"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertTriangle, TrendingDown, BarChart3, XCircle, Info, ArrowLeft, CheckCircle2, ShieldCheck, Skull, PartyPopper, Quote, Dices,
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

interface Benchmark {
  id: string;
  name_fa: string;
  win_rate_pct: number;
  profit_factor: number;
  kind: "fail" | "baseline" | "better" | "success" | "benchmark";
  note_fa: string;
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
  verdict_success_fa: string;
  verdict_success_detail_fa: string;
  benchmarks: Benchmark[];
  hero_badge: string;
  hero_title: string;
  robot_quote: string;
  tombstone_title: string;
  tombstone_epitaph: string;
  saved_what: string;
}

function faNum(v: number, digits: number = 0): string {
  return v.toLocaleString("fa-IR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function faPct(v: number, digits: number = 1): string {
  const abs = Math.abs(v);
  const sign = v < 0 ? "\u2212" : "";
  return `${sign}${faNum(abs, digits)}٪`;
}

export default function TSFreshBacktestVerdictPage() {
  const [data, setData] = useState<VerdictData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [simDots, setSimDots] = useState<boolean[] | null>(null);
  const [simHistory, setSimHistory] = useState<number[]>([]);

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

  const runSim = () => {
    const results: boolean[] = [];
    for (let i = 0; i < 100; i++) {
      results.push(Math.random() < 0.333);
    }
    setSimDots(results);
    const wr = (results.filter((r) => r).length / results.length) * 100;
    setSimHistory((prev) => [...prev, wr]);
  };

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

      {/* Hero: Saved from loss */}
      <Card className="border-emerald-500/40 bg-emerald-500/5">
        <CardContent className="pt-6 pb-6 text-center space-y-3">
          <Badge variant="outline" className="border-emerald-500/60 text-emerald-300 text-base px-4 py-1">
            <ShieldCheck className="h-4 w-4 mr-1" /> {data.hero_badge}
          </Badge>
          <h2 className="text-2xl font-bold text-emerald-400">{data.hero_title}</h2>
          {data.verdict_label_fa && (
            <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
              {data.verdict_label_fa}
            </p>
          )}
          <p className="text-xs text-muted-foreground max-w-xl mx-auto">
            {data.verdict_desc_fa}
          </p>
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 max-w-md mx-auto mt-4 flex items-center justify-center gap-2 text-sm text-emerald-200">
            <PartyPopper className="h-4 w-4" />
            <span>{data.saved_what}</span>
          </div>
        </CardContent>
      </Card>

      {/* Key Insight */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" /> چرا این نتیجه قطعی است؟
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
                {faPct(data.params.random_walk_wr_pct)}
              </div>
            </div>
            <div className="border rounded-lg p-2 bg-background/50">
              <div className="text-muted-foreground">break-even</div>
              <div className="font-mono text-base text-rose-400">
                {faPct(data.params.break_even_wr_pct)}
              </div>
            </div>
            <div className="border rounded-lg p-2 bg-background/50">
              <div className="text-muted-foreground">میانگین مشاهده</div>
              <div className="font-mono text-base text-amber-400">
                ~{faPct(data.tests.reduce((s, t) => s + t.win_rate_pct, 0) / data.tests.length, 0)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Random walk game (Gamification) */}
      <Card className="border-primary/30 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Dices className="h-4 w-4 text-primary" /> خودت تست کن: سکه‌ی تصادفی 🎲
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
            این دکمه <strong>۱۰۰ معامله کاملاً تصادفی</strong> (بدون هیچ سیگنالی) شبیه‌سازی می‌کند.
            در یک بازار تصادفی، احتمال برنده شدن ={" "}
            <span className="font-mono text-foreground">SL/(TP+SL) = ۲/۶ = ۳۳.۳٪</span>.
            حالا ببینید tsfresh هم همین عدد را می‌دهد — یعنی tsfresh هم مثل سکه بوده!
          </p>

          <div className="flex items-center gap-3 mb-4 flex-wrap">
            <button
              onClick={runSim}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm"
            >
              <Dices className="h-4 w-4" />
              {simDots ? "🎲 دوباره پرتاب کن" : "🎲 پرتاب ۱۰۰ سکه"}
            </button>
            {simDots && (
              <div className="text-sm flex items-center gap-2 flex-wrap">
                <span>
                  <strong className="text-emerald-400">{simDots.filter((d) => d).length}</strong> برد
                </span>
                <span className="text-border">|</span>
                <span>
                  <strong className="text-rose-400">{simDots.filter((d) => !d).length}</strong> باخت
                </span>
                <span className="text-border">|</span>
                <span className="font-mono">
                  <strong className="text-primary">
                    WR: {((simDots.filter((d) => d).length / simDots.length) * 100).toFixed(1)}٪
                  </strong>
                </span>
              </div>
            )}
          </div>

          {simDots && (
            <>
              <div className="flex flex-wrap gap-1 mb-4 p-2 bg-background/30 rounded-lg" dir="ltr">
                {simDots.map((win, i) => (
                  <div
                    key={i}
                    className={`w-3 h-3 rounded-sm ${win ? "bg-emerald-500/80" : "bg-rose-500/80"}`}
                    title={win ? "برد" : "باخت"}
                  />
                ))}
              </div>

              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-emerald-300">
                  <PartyPopper className="h-4 w-4" />
                  دیدی؟ تصادف هم همین ~۳۳٪ را داد!
                </div>
                <p className="text-xs text-muted-foreground">
                  اگر tsfresh edge داشت، WR آن باید <strong>&gt; ۴۴.۲٪</strong> می‌شد. نشد.
                  یعنی tsfresh دقیقاً مثل این سکه عمل می‌کرد.
                </p>
                {simHistory.length > 1 && (
                  <p className="text-xs text-foreground/80 border-t border-emerald-500/20 pt-2 mt-2">
                    🎯 <strong>آمار {simHistory.length} پرتاب:</strong>{" "}
                    میانگین {(simHistory.reduce((a, b) => a + b, 0) / simHistory.length).toFixed(1)}٪
                    {" — "}
                    tsfresh baseline: <span className="font-mono">۳۳.۰٪</span>
                    {" — "}
                    {Math.abs(simHistory.reduce((a, b) => a + b, 0) / simHistory.length - 33.0) < 2
                      ? "تقریباً یکسان! ✓"
                      : "داری به ۳۳.۳٪ نزدیک می‌شوی..."}
                  </p>
                )}
              </div>
            </>
          )}
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
                    <td className="py-2 px-3 text-right font-mono text-xs">{faNum(t.n_matches)}</td>
                    <td className="py-2 px-3 text-right font-mono text-xs">{faNum(t.horizon_h)} ساعت</td>
                    <td className="py-2 px-3 text-right font-mono text-xs">{faNum(t.trades)}</td>
                    <td className={`py-2 px-3 text-right font-mono text-xs ${t.win_rate_pct >= data.params.break_even_wr_pct ? "text-emerald-400" : "text-rose-400"}`}>
                      {faPct(t.win_rate_pct)}
                    </td>
                    <td className={`py-2 px-3 text-right font-mono text-xs ${t.profit_factor >= 1 ? "text-emerald-400" : "text-rose-400"}`}>
                      {faNum(t.profit_factor, 2)}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-xs text-rose-400">
                      {faPct(t.max_dd_pct, 1)}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <Badge variant="outline" className="border-slate-500/40 text-slate-400 text-xs">
                        آرشیو
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
                break-even: {faPct(data.params.break_even_wr_pct)}
              </span>
            </div>
            <div className="absolute inset-0 flex items-end justify-around px-2">
              {data.tests.map((t) => (
                <div
                  key={t.id}
                  className="w-[12%] bg-rose-500/60 rounded-t hover:bg-rose-500/80 transition-colors"
                  style={{ height: `${(t.win_rate_pct / maxY) * 100}%` }}
                  title={`${t.id}: ${faPct(t.win_rate_pct)}`}
                />
              ))}
            </div>
          </div>
          <div className="flex justify-around px-2 mt-2">
            {data.tests.map((t) => (
              <div key={t.id} className="w-[12%] text-center">
                <div className="text-xs font-mono text-rose-400">{faPct(t.win_rate_pct)}</div>
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
            <XCircle className="h-4 w-4 text-slate-400" /> فرضیه‌های رد شده
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

      {/* Benchmark: fail = success of process */}
      <Card className="border-emerald-500/30 bg-emerald-500/5">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> fail tsfresh = پیروزی فرایند
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Badge variant="outline" className="border-emerald-500/60 text-emerald-300 mb-3">
            <CheckCircle2 className="h-3 w-3 mr-1" /> No edge, but no loss
          </Badge>
          <p className="text-sm leading-relaxed text-foreground/90 mb-2">
            <strong>{data.verdict_success_fa}</strong>
          </p>
          <p className="text-sm leading-relaxed text-muted-foreground mb-4">
            {data.verdict_success_detail_fa}
          </p>

          <div className="overflow-x-auto rounded-lg border border-border/50">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 text-xs text-muted-foreground">
                <tr>
                  <th className="text-right py-2 px-3 font-normal">استراتژی</th>
                  <th className="text-right py-2 px-3 font-normal">WR</th>
                  <th className="text-right py-2 px-3 font-normal">PF</th>
                  <th className="text-right py-2 px-3 font-normal">توضیح</th>
                </tr>
              </thead>
              <tbody>
                {data.benchmarks.map((b) => {
                  const pfColor =
                    b.kind === "success" ? "text-emerald-400" :
                    b.kind === "better" ? "text-amber-400" :
                    b.kind === "benchmark" ? "text-muted-foreground" :
                    "text-rose-400";
                  return (
                    <tr key={b.id} className="border-t border-border/30 hover:bg-muted/20 transition-colors">
                      <td className="py-2 px-3 text-right text-xs">{b.name_fa}</td>
                      <td className="py-2 px-3 text-right font-mono text-xs">{b.win_rate_pct > 0 ? faPct(b.win_rate_pct) : "—"}</td>
                      <td className={`py-2 px-3 text-right font-mono text-xs ${pfColor}`}>
                        {b.profit_factor > 0 ? faNum(b.profit_factor, 2) : "—"}
                      </td>
                      <td className="py-2 px-3 text-right text-xs text-muted-foreground">{b.note_fa}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-5">
            <div className="text-xs text-muted-foreground mb-2">مقایسه Profit Factor — خط قرمز = مرز سوددهی (PF=۱.۰)</div>
            <div className="space-y-2">
              {data.benchmarks.filter((b) => b.profit_factor > 0).map((b) => {
                const color =
                  b.kind === "success" ? "bg-emerald-500" :
                  b.kind === "better" ? "bg-amber-500" :
                  b.kind === "baseline" ? "bg-slate-500" :
                  "bg-rose-500";
                const maxPF = 1.5;
                const widthPct = Math.min((b.profit_factor / maxPF) * 100, 100);
                const lineLeftPct = (1.0 / maxPF) * 100;
                return (
                  <div key={b.id} className="flex items-center gap-2 text-xs">
                    <span className="w-36 text-muted-foreground text-right text-[11px]">{b.name_fa}</span>
                    <div className="flex-1 bg-muted/30 rounded h-5 relative overflow-hidden">
                      <div className={`${color} h-full rounded`} style={{ width: `${widthPct}%` }} />
                      <div
                        className="absolute top-0 bottom-0 border-l-2 border-rose-500/70"
                        style={{ left: `${lineLeftPct}%` }}
                        title="PF=1.0 (break-even)"
                      />
                    </div>
                    <span className={`w-10 text-left font-mono ${b.profit_factor >= 1.0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {faNum(b.profit_factor, 2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <p className="text-xs text-muted-foreground mt-4">
            نکته: Nooaah Q4-۲۰۲۳ تنها موردی است که PF بالای ۱.۰ دارد (دوره صعودی — خارج از نمونه). SarvRouter (gate) در ADR-0034 با ۲۴۰ switch و ۰ kill، پایداری نشان داد.
          </p>
        </CardContent>
      </Card>

      {/* Tombstone (Fun) */}
      <Card className="border-border/50 bg-slate-900/50 text-center py-8 relative overflow-hidden">
        <CardContent>
          <div className="flex justify-center mb-4">
            <div className="bg-slate-800 p-4 rounded-full border border-slate-700">
              <Skull className="h-8 w-8 text-slate-400" />
            </div>
          </div>
          <h3 className="text-lg font-bold text-slate-300 mb-2">{data.tombstone_title}</h3>
          <p className="text-sm text-slate-400 italic mb-6">
            "{data.tombstone_epitaph}"
          </p>
          <div className="inline-block bg-muted/20 border border-border/50 rounded-xl p-4 max-w-lg mx-auto">
            <Quote className="h-4 w-4 text-primary mb-2 mx-auto opacity-50" />
            <p className="text-sm text-foreground/80 font-medium">
              {data.robot_quote}
            </p>
          </div>
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
