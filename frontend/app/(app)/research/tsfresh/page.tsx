"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp, TrendingDown, Activity, Clock, AlertTriangle, BarChart3,
  ArrowRight, ChevronDown, ChevronRight, Info, Zap,
  ArrowUpDown, ArrowUp, ArrowDown
} from "lucide-react";

interface SimilarPeriod {
  date: string;
  similarity: number;
  forward_return_24h_pct: number;
}

interface Stats {
  n: number;
  mean_return_24h_pct: number;
  median_return_24h_pct: number;
  std_return_24h_pct: number;
  positive_pct: number;
  min_return_24h_pct: number;
  max_return_24h_pct: number;
}

interface SimilarityData {
  as_of: string;
  current_datetime: string;
  current_price: number;
  current_regime: string;
  window_hours: number;
  horizon_hours: number;
  n_features: number;
  feature_names: string[];
  current_features: Record<string, number | null>;
  similar_periods: SimilarPeriod[];
  stats: Stats;
  disclaimer: string;
}

const FEATURE_LABELS: Record<string, string> = {
  ret_1_mean: "میانگین بازده ۱h",
  ret_1_std: "انحراف معیار بازده ۱h",
  ret_24: "بازده ۲۴h",
  rsi_14_mean: "میانگین RSI(14)",
  rsi_14_last: "آخرین RSI(14)",
  atr_14_mean: "میانگین ATR(14)",
  atr_14_std: "انحراف معیار ATR(14)",
  atr_pct_mean: "ATR% میانگین",
  ema_ratio_mean: "نسبت EMA20/EMA50",
  macd_mean: "میانگین MACD",
  macd_hist_mean: "میانگین MACD Histogram",
  vol_ratio_mean: "نسبت حجم به میانگین",
  vol_ratio_std: "انحراف معیار نسبت حجم",
  volatility: "نوسان‌پذیری",
  close_position: "موقعیت close در دامنه",
  hh_ll_ratio: "نسبت High-Low به Close",
  upper_wick_mean: "میانگین سایه بالایی",
  lower_wick_mean: "میانگین سایه پایینی",
  body_ratio_mean: "میانگین نسبت بدنه",
};

type Tone = "bullish" | "bearish" | "neutral" | "extreme-bull" | "extreme-bear";

function featureTone(key: string, v: number | null): Tone {
  if (v === null || v === undefined) return "neutral";
  switch (key) {
    case "rsi_14_last":
    case "rsi_14_mean":
      if (v > 70) return "extreme-bull";
      if (v < 30) return "extreme-bear";
      if (v > 55) return "bullish";
      if (v < 45) return "bearish";
      return "neutral";
    case "macd_hist_mean":
    case "macd_mean":
      if (v > 0) return "bullish";
      if (v < 0) return "bearish";
      return "neutral";
    case "ema_ratio_mean":
      if (v > 0.005) return "bullish";
      if (v < -0.005) return "bearish";
      return "neutral";
    case "ret_1_mean":
    case "ret_24":
      if (v > 0) return "bullish";
      if (v < 0) return "bearish";
      return "neutral";
    case "close_position":
      if (v > 0.8) return "extreme-bull";
      if (v < 0.2) return "extreme-bear";
      return "neutral";
    case "vol_ratio_mean":
    case "volatility":
    case "atr_pct_mean":
      if (v > 1.5) return "extreme-bull";
      return "neutral";
    default:
      return "neutral";
  }
}

const TONE_STYLE: Record<Tone, string> = {
  "bullish": "border-emerald-500/30 bg-emerald-500/5",
  "bearish": "border-rose-500/30 bg-rose-500/5",
  "extreme-bull": "border-amber-500/40 bg-amber-500/8",
  "extreme-bear": "border-cyan-500/40 bg-cyan-500/8",
  "neutral": "border-border bg-muted/20",
};

const TONE_VALUE_STYLE: Record<Tone, string> = {
  "bullish": "text-emerald-300",
  "bearish": "text-rose-300",
  "extreme-bull": "text-amber-300",
  "extreme-bear": "text-cyan-300",
  "neutral": "text-foreground",
};

function formatPct(v: number, digits = 2): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("fa-IR", { year: "numeric", month: "2-digit", day: "2-digit" });
  } catch {
    return iso.slice(0, 10);
  }
}

function dataFreshness(as_of: string): { label: string; tone: "green" | "yellow" | "red" } {
  try {
    const t = new Date(as_of).getTime();
    const days = (Date.now() - t) / (1000 * 60 * 60 * 24);
    if (days <= 2) return { label: `${Math.round(days)} روز پیش`, tone: "green" };
    if (days <= 7) return { label: `${Math.round(days)} روز پیش`, tone: "yellow" };
    return { label: `${Math.round(days)} روز پیش`, tone: "red" };
  } catch {
    return { label: "—", tone: "yellow" };
  }
}

type SortKey = "date" | "similarity" | "return";
type SortDir = "asc" | "desc";

function SortIcon({ col, sortConfig }: { col: SortKey; sortConfig: { key: SortKey; dir: SortDir } }) {
  if (sortConfig.key !== col) return <ArrowUpDown className="h-3 w-3 opacity-30" />;
  return sortConfig.dir === "asc" ? <ArrowUp className="h-3 w-3 text-primary" /> : <ArrowDown className="h-3 w-3 text-primary" />;
}

function HistoricalTable({ periods }: { periods: SimilarPeriod[] }) {
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; dir: SortDir }>({ key: "similarity", dir: "desc" });

  const sortedPeriods = useMemo(() => {
    const sorted = [...periods];
    sorted.sort((a, b) => {
      let valA, valB;
      if (sortConfig.key === "date") {
        valA = new Date(a.date).getTime();
        valB = new Date(b.date).getTime();
      } else if (sortConfig.key === "similarity") {
        valA = a.similarity;
        valB = b.similarity;
      } else {
        valA = a.forward_return_24h_pct;
        valB = b.forward_return_24h_pct;
      }
      if (valA < valB) return sortConfig.dir === "asc" ? -1 : 1;
      if (valA > valB) return sortConfig.dir === "asc" ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [periods, sortConfig]);

  const maxAbs = Math.max(...periods.map((p) => Math.abs(p.forward_return_24h_pct)), 1);
  const positiveCount = periods.filter((p) => p.forward_return_24h_pct > 0).length;
  const negativeCount = periods.length - positiveCount;

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => ({
      key,
      dir: prev.key === key && prev.dir === "desc" ? "asc" : "desc",
    }));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Badge variant="outline" className="border-emerald-500/40 text-emerald-300">
          {positiveCount} مثبت
        </Badge>
        <Badge variant="outline" className="border-rose-500/40 text-rose-300">
          {negativeCount} منفی
        </Badge>
        <span className="ml-auto">مجموع {periods.length} مورد</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border/50">
        <table className="w-full text-sm">
          <thead className="bg-muted/30">
            <tr className="text-xs text-muted-foreground select-none">
              <th className="text-right py-2 px-3 font-normal">#</th>
              <th className="text-right py-2 px-3 font-normal cursor-pointer hover:text-foreground" onClick={() => handleSort("date")}>
                <div className="flex items-center gap-1 justify-end">تاریخ <SortIcon col="date" sortConfig={sortConfig} /></div>
              </th>
              <th className="text-left py-2 px-3 font-normal cursor-pointer hover:text-foreground" onClick={() => handleSort("similarity")}>
                <div className="flex items-center gap-1">شباهت <SortIcon col="similarity" sortConfig={sortConfig} /></div>
              </th>
              <th className="text-right py-2 px-3 font-normal cursor-pointer hover:text-foreground" onClick={() => handleSort("return")}>
                <div className="flex items-center gap-1 justify-end">بازده ۲۴h <SortIcon col="return" sortConfig={sortConfig} /></div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedPeriods.map((p, i) => {
              const positive = p.forward_return_24h_pct >= 0;
              const widthPct = (Math.abs(p.forward_return_24h_pct) / maxAbs) * 100;
              return (
                <tr key={`${p.date}-${i}`} className="border-t border-border/30 hover:bg-muted/20 transition-colors">
                  <td className="py-2 px-3 text-right text-muted-foreground font-mono text-xs">{i + 1}</td>
                  <td className="py-2 px-3 text-right font-mono text-xs" title={p.date}>{formatDate(p.date)}</td>
                  <td className="py-2 px-3 text-left">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-muted/40 rounded-full h-1.5 overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: `${p.similarity * 100}%` }} />
                      </div>
                      <span className="font-mono text-xs text-muted-foreground">{(p.similarity * 100).toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="py-2 px-3 text-left">
                    <div className="flex items-center gap-2 justify-end">
                      <div className="flex-1 bg-muted/30 rounded h-4 relative overflow-hidden max-w-[120px]">
                        <div className={`h-full rounded ${positive ? "bg-emerald-500/70" : "bg-rose-500/70"}`} style={{ width: `${widthPct}%` }} />
                      </div>
                      <span className={`font-mono text-xs w-14 text-left ${positive ? "text-emerald-400" : "text-rose-400"}`}>
                        {formatPct(p.forward_return_24h_pct)}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function HowItWorks() {
  const [open, setOpen] = useState(false);
  return (
    <Card className="border-border/50">
      <button onClick={() => setOpen((o) => !o)} className="w-full flex items-center justify-between p-4 hover:bg-muted/20 transition-colors rounded-t-lg" type="button">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Info className="h-4 w-4 text-primary" /> چطور این تحلیل کار می‌کند؟
        </div>
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>
      {open && (
        <CardContent className="pt-0 text-xs text-muted-foreground space-y-3 leading-relaxed">
          <div><strong className="text-foreground">۱. الگوی فعلی:</strong> ۱۹ ویژگی (RSI, ATR, MACD, حجم، نوسان) از ۲۴ ساعت اخیر BTC استخراج می‌شود.</div>
          <div><strong className="text-foreground">۲. شباهت تاریخی:</strong> این الگو با ۵۰,۹۶۸ پنجره‌ی ۲۴ ساعته‌ی ۵ سال گذشته (از ۲۰۲۱) مقایسه می‌شود با شباهت کسینوسی (Cosine Similarity) روی featureهای Z-score شده.</div>
          <div><strong className="text-foreground">۳. ۵۰ دوره برتر:</strong> با N=۵۰ (طبق AP-58، حداقل ۳۰ برای معناداری آماری)، همه‌ی دوره‌های مشابه انتخاب می‌شوند.</div>
          <div><strong className="text-foreground">۴. بازده ۲۴h بعد:</strong> برای هر ۵۰ دوره، بازده ۲۴ ساعته‌ی بعد از آن محاسبه می‌شود. میانگین، میانه، درصد مثبت، و توزیع، خلاصه‌ی رفتار تاریخی است.</div>
          <div className="pt-2 border-t border-border/30"><strong className="text-foreground">⚠️ هشدار:</strong> این یک ابزار <strong>تحلیلی</strong> است، نه <strong>سیگنال معاملاتی</strong>. هزینه‌ی round-trip معامله (۰.۶۵٪) در آمار لحاظ نشده — اگر میانگین کمتر از این عدد باشد، در عمل edge وجود ندارد (طبق AP-39).</div>
        </CardContent>
      )}
    </Card>
  );
}

function TimeframeStats({ periods, asOfDate }: { periods: SimilarPeriod[]; asOfDate: string }) {
  const stats = useMemo(() => {
    const now = new Date(asOfDate).getTime();
    const sixMonthsAgo = now - 6 * 30 * 24 * 60 * 60 * 1000;
    const oneYearAgo = now - 365 * 24 * 60 * 60 * 1000;

    const filterBy = (since: number) => periods.filter((p) => new Date(p.date).getTime() >= since);
    
    const calc = (arr: SimilarPeriod[]) => {
      if (arr.length === 0) return { n: 0, pos: 0, neg: 0, posPct: 0 };
      const pos = arr.filter((p) => p.forward_return_24h_pct > 0).length;
      return { n: arr.length, pos, neg: arr.length - pos, posPct: (pos / arr.length) * 100 };
    };

    return {
      m6: calc(filterBy(sixMonthsAgo)),
      y1: calc(filterBy(oneYearAgo)),
    };
  }, [periods, asOfDate]);

  return (
    <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-border/30">
      <div className="bg-muted/10 border rounded-lg p-3">
        <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
          <Clock className="h-3 w-3" /> ۶ ماه اخیر (نسبت به دیتا)
        </div>
        <div className="flex justify-between items-end">
          <div className="text-sm">
            <span className="text-emerald-400 font-bold">{stats.m6.pos}</span> مثبت
            <span className="mx-2 text-border">|</span>
            <span className="text-rose-400 font-bold">{stats.m6.neg}</span> منفی
          </div>
          <div className="text-xs text-muted-foreground font-mono">{stats.m6.n} مورد</div>
        </div>
        <div className="w-full bg-muted/40 rounded-full h-1.5 mt-2 overflow-hidden flex">
          <div className="bg-emerald-500 h-full" style={{ width: `${stats.m6.posPct}%` }} />
          <div className="bg-rose-500 h-full" style={{ width: `${100 - stats.m6.posPct}%` }} />
        </div>
      </div>
      
      <div className="bg-muted/10 border rounded-lg p-3">
        <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
          <Clock className="h-3 w-3" /> ۱ سال اخیر (نسبت به دیتا)
        </div>
        <div className="flex justify-between items-end">
          <div className="text-sm">
            <span className="text-emerald-400 font-bold">{stats.y1.pos}</span> مثبت
            <span className="mx-2 text-border">|</span>
            <span className="text-rose-400 font-bold">{stats.y1.neg}</span> منفی
          </div>
          <div className="text-xs text-muted-foreground font-mono">{stats.y1.n} مورد</div>
        </div>
        <div className="w-full bg-muted/40 rounded-full h-1.5 mt-2 overflow-hidden flex">
          <div className="bg-emerald-500 h-full" style={{ width: `${stats.y1.posPct}%` }} />
          <div className="bg-rose-500 h-full" style={{ width: `${100 - stats.y1.posPct}%` }} />
        </div>
      </div>
    </div>
  );
}

export default function TSFreshResearchPage() {
  const [data, setData] = useState<SimilarityData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/similarity.json")
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="container py-8">
        <Card className="border-rose-500/30">
          <CardHeader><CardTitle className="text-rose-400 flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> خطا در بارگذاری داده</CardTitle></CardHeader>
          <CardContent><p className="text-sm text-muted-foreground">{error}</p></CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container py-8 space-y-4">
        <Skeleton className="h-8 w-64" /><Skeleton className="h-40 w-full" /><Skeleton className="h-40 w-full" /><Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const { stats } = data;
  const freshness = dataFreshness(data.as_of);
  const freshColor = freshness.tone === "green" ? "border-emerald-500/40 text-emerald-300" : freshness.tone === "yellow" ? "border-amber-500/40 text-amber-300" : "border-rose-500/40 text-rose-300";
  const fee = 0.65;
  const meanAboveFee = stats.mean_return_24h_pct > fee;

  const buckets = [
    { label: "< -3%", min: -Infinity, max: -3, count: 0, color: "bg-rose-500/70" },
    { label: "-3% → -1%", min: -3, max: -1, count: 0, color: "bg-rose-400/70" },
    { label: "-1% → +1%", min: -1, max: 1, count: 0, color: "bg-slate-400/70" },
    { label: "+1% → +3%", min: 1, max: 3, count: 0, color: "bg-emerald-400/70" },
    { label: "> +3%", min: 3, max: Infinity, count: 0, color: "bg-emerald-500/70" },
  ];
  data.similar_periods.forEach((p) => {
    const v = p.forward_return_24h_pct;
    const b = buckets.find((bk) => v >= bk.min && v < bk.max);
    if (b) b.count += 1;
  });
  const maxCount = Math.max(...buckets.map((b) => b.count), 1);

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Activity className="h-6 w-6 text-primary" /> تحلیل تشابه تاریخی BTC</h1>
          <p className="text-sm text-muted-foreground mt-1">الگوی ۲۴ ساعت اخیر BTC، با ۵ سال گذشته مقایسه می‌شود.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className="text-xs">Research · Insight only</Badge>
          <Badge variant="outline" className={`text-xs ${freshColor}`}><Clock className="h-3 w-3 mr-1" /> داده {freshness.label}</Badge>
        </div>
      </div>

      {/* Meta card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><div className="text-muted-foreground text-xs mb-1">آخرین داده</div><div className="font-mono text-xs">{data.current_datetime}</div></div>
            <div><div className="text-muted-foreground text-xs mb-1">قیمت</div><div className="font-mono">${data.current_price.toLocaleString()}</div></div>
            <div><div className="text-muted-foreground text-xs mb-1">پنجره</div><div>{data.window_hours}h الگو</div></div>
            <div><div className="text-muted-foreground text-xs mb-1">افق پیش‌بینی</div><div>{data.horizon_hours}h آینده</div></div>
          </div>
        </CardContent>
      </Card>

      <HowItWorks />

      {/* Section 1: Current Pattern */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" /> ۱. الگوی فعلی
            <span className="text-xs font-normal text-muted-foreground mr-auto">{data.n_features} ویژگی · رنگ‌بندی معنادار</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {data.feature_names.map((f) => {
              const v = data.current_features[f];
              const tone = featureTone(f, v);
              return (
                <div key={f} className={`border rounded-lg p-2.5 transition-colors ${TONE_STYLE[tone]}`} title={FEATURE_LABELS[f] ?? f}>
                  <div className="text-xs text-muted-foreground truncate">{FEATURE_LABELS[f] ?? f}</div>
                  <div className={`font-mono text-sm mt-0.5 ${TONE_VALUE_STYLE[tone]}`}>{v === null || v === undefined ? "—" : Number.isInteger(v) ? v : v.toFixed(4)}</div>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground mt-3 flex items-center gap-1"><Info className="h-3 w-3" /> سبز = صعودی · قرمز = نزولی · کهربایی = اشباع خرید/نوسان بالا · فیروزه‌ای = اشباع فروش</p>
        </CardContent>
      </Card>

      {/* Section 2: Similar Periods */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4" /> ۲. {data.similar_periods.length} دوره‌ی مشابه تاریخی
            <span className="text-xs font-normal text-muted-foreground mr-auto">برای مرتب‌سازی، روی هدر کلیک کنید</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <HistoricalTable periods={data.similar_periods} />
        </CardContent>
      </Card>

      {/* Section 3: Forward Returns */}
      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><TrendingUp className="h-4 w-4" /> ۳. بازده ۲۴h بعد از الگوهای مشابه</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="border rounded-lg p-3 bg-muted/10"><div className="text-xs text-muted-foreground">میانگین</div><div className={`font-mono text-lg ${stats.mean_return_24h_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatPct(stats.mean_return_24h_pct)}</div></div>
            <div className="border rounded-lg p-3 bg-muted/10"><div className="text-xs text-muted-foreground">میانه</div><div className={`font-mono text-lg ${stats.median_return_24h_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatPct(stats.median_return_24h_pct)}</div></div>
            <div className="border rounded-lg p-3 bg-muted/10"><div className="text-xs text-muted-foreground">درصد مثبت</div><div className={`font-mono text-lg ${stats.positive_pct >= 55 ? "text-emerald-400" : stats.positive_pct >= 45 ? "text-amber-400" : "text-rose-400"}`}>{stats.positive_pct.toFixed(1)}%</div></div>
            <div className="border rounded-lg p-3 bg-muted/10"><div className="text-xs text-muted-foreground">تعداد (N)</div><div className="font-mono text-lg flex items-center gap-1">{stats.n}{stats.n >= 30 && <span className="text-xs text-emerald-400">✓</span>}</div></div>
          </div>

          {/* New: Timeframe Stats */}
          <TimeframeStats periods={data.similar_periods} asOfDate={data.current_datetime} />

          {/* Fee comparison bar */}
          <div className="pt-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span className="flex items-center gap-1"><Zap className="h-3 w-3" /> میانگین بازده در برابر هزینه معامله</span>
              <span className={meanAboveFee ? "text-emerald-400" : "text-rose-400"}>{meanAboveFee ? "بالاتر از هزینه ✓" : "کمتر از هزینه ⚠️"}</span>
            </div>
            <div className="relative h-6 bg-muted/30 rounded overflow-hidden">
              {(() => {
                const scale = Math.max(Math.abs(stats.mean_return_24h_pct), fee * 2);
                const center = 50;
                const meanWidth = (stats.mean_return_24h_pct / (scale * 2)) * 100;
                const feeWidth = (fee / (scale * 2)) * 100;
                return (
                  <>
                    <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border/50" />
                    <div className="absolute top-0 bottom-0 bg-amber-500/20 border-l border-amber-500/50" style={{ left: `${center + feeWidth}%`, width: `${feeWidth}%` }} />
                    <div className="absolute top-0 bottom-0 bg-amber-500/20 border-r border-amber-500/50" style={{ right: `${center + feeWidth}%`, width: `${feeWidth}%` }} />
                    <div className={`absolute top-1 bottom-1 ${stats.mean_return_24h_pct >= 0 ? "bg-emerald-500/70" : "bg-rose-500/70"} rounded`} style={{ left: stats.mean_return_24h_pct >= 0 ? `${center}%` : `${center + meanWidth}%`, width: `${Math.abs(meanWidth)}%` }} />
                  </>
                );
              })()}
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground mt-1"><span>—</span><span>۰</span><span>+</span></div>
            <p className="text-xs text-muted-foreground mt-1">ناحیه کهربایی: هزینه round-trip ({fee.toFixed(2)}٪) — برای edge واقعی، بازده باید از این ناحیه فراتر برود.</p>
          </div>

          {/* Histogram */}
          <div>
            <div className="text-xs text-muted-foreground mb-2">توزیع بازده (۵ بازه)</div>
            <div className="space-y-1.5">
              {buckets.map((b) => {
                const pct = (b.count / data.similar_periods.length) * 100;
                return (
                  <div key={b.label} className="flex items-center gap-2 text-xs">
                    <span className="w-24 text-muted-foreground text-left font-mono">{b.label}</span>
                    <div className="flex-1 bg-muted/30 rounded h-5 relative overflow-hidden"><div className={`${b.color} h-full rounded transition-all`} style={{ width: `${(b.count / maxCount) * 100}%` }} /></div>
                    <span className="w-16 text-right font-mono text-muted-foreground">{b.count} ({pct.toFixed(0)}%)</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs pt-2 border-t border-border/30">
            <div className="flex items-center gap-2"><TrendingDown className="h-3 w-3 text-rose-400" /><span className="text-muted-foreground">حداقل بازده:</span><span className="font-mono text-rose-400">{formatPct(stats.min_return_24h_pct)}</span></div>
            <div className="flex items-center gap-2"><TrendingUp className="h-3 w-3 text-emerald-400" /><span className="text-muted-foreground">حداکثر بازده:</span><span className="font-mono text-emerald-400">{formatPct(stats.max_return_24h_pct)}</span></div>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2 text-xs text-amber-200/90">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div><strong>هشدار:</strong> این یک ابزار تحلیل تاریخی است، نه سیگنال معاملاتی. الگوهای گذشته ممکن است تکرار نشوند. هزینه‌ی round-trip معامله (۰.۶۵٪) در این تحلیل لحاظ نشده است.
              {stats.mean_return_24h_pct < 0.65 && <span className="block mt-1">⚠️ میانگین بازده ({stats.mean_return_24h_pct.toFixed(2)}%) کمتر از هزینه‌ی معامله (۰.۶۵٪) است.</span>}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-xs text-muted-foreground text-center pt-2 space-y-1">
        <p>as_of: <span className="font-mono">{data.as_of}</span></p>
        <p>داده: BTCUSDT (Binance) · {data.n_features} feature · {data.similar_periods.length} match (N&gt;30, AP-58)</p>
        <Link href="/" className="inline-flex items-center gap-1 mt-2 text-primary hover:underline">بازگشت <ArrowRight className="h-3 w-3" /></Link>
      </div>
    </div>
  );
}
