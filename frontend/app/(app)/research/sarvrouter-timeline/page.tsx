"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Activity, Clock, AlertTriangle, Info, ArrowRight,
  TrendingUp, TrendingDown, Minus, CheckCircle2, XCircle,
  ArrowUpDown, ArrowUp, ArrowDown, Filter,
} from "lucide-react";

interface Switch {
  index: number;
  date: string;
  price: number;
  regime: string;
  prev_regime: string;
  forward_24h_pct: number | null;
  forward_168h_pct: number | null;
  forward_720h_pct: number | null;
  correct_24h: string | null;
}

interface RegimeStat {
  total: number;
  correct_24h: number;
  incorrect_24h: number;
  accuracy_pct: number;
}

interface Data {
  as_of: string;
  data_source: string;
  note: string;
  first_date: string;
  last_date: string;
  total_candles: number;
  total_switches: number;
  overall_accuracy_24h: { total: number; correct: number; accuracy_pct: number };
  stats: Record<string, RegimeStat>;
  switches: Switch[];
}

const REGIME_META: Record<string, { label: string; icon: any; color: string }> = {
  uptrend: { label: "صعودی", icon: TrendingUp, color: "text-emerald-400" },
  downtrend: { label: "نزولی", icon: TrendingDown, color: "text-rose-400" },
  range: { label: "رنج", icon: Minus, color: "text-amber-400" },
  unknown: { label: "نامشخص", icon: AlertTriangle, color: "text-muted-foreground" },
};

function fmtPct(v: number | null): string {
  if (v === null || v === undefined) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function fmtDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("fa-IR", { year: "numeric", month: "2-digit", day: "2-digit" });
  } catch {
    return iso.slice(0, 10);
  }
}

type SortKey = "date" | "fwd24" | "fwd168";
type SortDir = "asc" | "desc";

function SortIcon({ col, sortConfig }: { col: SortKey; sortConfig: { key: SortKey; dir: SortDir } }) {
  if (sortConfig.key !== col) return <ArrowUpDown className="h-3 w-3 opacity-30" />;
  return sortConfig.dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />;
}

export default function SarvRouterTimelinePage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({ key: "date", dir: "desc" });

  useEffect(() => {
    fetch("/data/sarvrouter-decisions.json")
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    let arr = data.switches;
    if (filter !== "all") arr = arr.filter(s => s.regime === filter);
    const sorted = [...arr];
    sorted.sort((a, b) => {
      let va: any, vb: any;
      if (sort.key === "date") { va = new Date(a.date).getTime(); vb = new Date(b.date).getTime(); }
      else if (sort.key === "fwd24") { va = a.forward_24h_pct ?? -999; vb = b.forward_24h_pct ?? -999; }
      else { va = a.forward_168h_pct ?? -999; vb = b.forward_168h_pct ?? -999; }
      if (va < vb) return sort.dir === "asc" ? -1 : 1;
      if (va > vb) return sort.dir === "asc" ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [data, filter, sort]);

  const handleSort = (key: SortKey) => {
    setSort(prev => ({ key, dir: prev.key === key && prev.dir === "desc" ? "asc" : "desc" }));
  };

  if (error) {
    return (
      <div className="container py-8">
        <Card className="border-rose-500/30">
          <CardHeader><CardTitle className="text-rose-400 flex items-center gap-2"><AlertTriangle className="h-5 w-5" />خطا</CardTitle></CardHeader>
          <CardContent><p className="text-sm text-muted-foreground">{error}</p></CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return <div className="container py-8 space-y-4"><Skeleton className="h-8 w-64" /><Skeleton className="h-40 w-full" /><Skeleton className="h-96 w-full" /></div>;
  }

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            تاریخچه تصمیم‌های SarvRouter
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data.total_switches.toLocaleString()} تصمیم در {data.total_candles.toLocaleString()} کندل
          </p>
        </div>
        <Badge variant="outline" className="text-xs">Research · Insight only</Badge>
      </div>

      {/* Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-muted-foreground">بازه</div>
              <div className="font-mono text-xs">{data.first_date.slice(0,10)} → {data.last_date.slice(0,10)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">کل تصمیم‌ها</div>
              <div className="text-lg font-bold">{data.total_switches.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">دقت کل (24h)</div>
              <div className={`text-lg font-bold ${data.overall_accuracy_24h.accuracy_pct > 55 ? "text-emerald-400" : data.overall_accuracy_24h.accuracy_pct > 50 ? "text-amber-400" : "text-rose-400"}`}>
                {data.overall_accuracy_24h.accuracy_pct}%
              </div>
              <div className="text-xs text-muted-foreground">{data.overall_accuracy_24h.correct}/{data.overall_accuracy_24h.total}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">data source</div>
              <div className="font-mono text-xs">{data.data_source}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Per-regime stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(data.stats).map(([regime, s]) => {
          const meta = REGIME_META[regime] || REGIME_META.unknown;
          const Icon = meta.icon;
          return (
            <Card key={regime}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-2">
                  <Icon className={`h-4 w-4 ${meta.color}`} />
                  <span className="text-sm font-medium">{meta.label}</span>
                </div>
                <div className={`text-2xl font-bold ${s.accuracy_pct > 55 ? "text-emerald-400" : s.accuracy_pct > 50 ? "text-amber-400" : "text-rose-400"}`}>
                  {s.accuracy_pct}%
                </div>
                <div className="text-xs text-muted-foreground">{s.correct_24h}/{s.total} درست</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Filter + Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Filter className="h-4 w-4" />
              تصمیم‌ها ({filtered.length.toLocaleString()})
            </CardTitle>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-background border border-border rounded px-2 py-1 text-xs"
            >
              <option value="all">همه رژیم‌ها</option>
              <option value="uptrend">صعودی</option>
              <option value="downtrend">نزولی</option>
              <option value="range">رنج</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border border-border/50 max-h-[600px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 sticky top-0">
                <tr className="text-xs text-muted-foreground select-none">
                  <th className="text-right py-2 px-2 font-normal">#</th>
                  <th className="text-right py-2 px-2 font-normal cursor-pointer hover:text-foreground" onClick={() => handleSort("date")}>
                    <div className="flex items-center gap-1 justify-end">تاریخ <SortIcon col="date" sortConfig={sort} /></div>
                  </th>
                  <th className="text-right py-2 px-2 font-normal">رژیم</th>
                  <th className="text-left py-2 px-2 font-normal">قیمت</th>
                  <th className="text-left py-2 px-2 font-normal cursor-pointer hover:text-foreground" onClick={() => handleSort("fwd24")}>
                    <div className="flex items-center gap-1">24h <SortIcon col="fwd24" sortConfig={sort} /></div>
                  </th>
                  <th className="text-left py-2 px-2 font-normal cursor-pointer hover:text-foreground" onClick={() => handleSort("fwd168")}>
                    <div className="flex items-center gap-1">7d <SortIcon col="fwd168" sortConfig={sort} /></div>
                  </th>
                  <th className="text-center py-2 px-2 font-normal">درست؟</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s, i) => {
                  const meta = REGIME_META[s.regime] || REGIME_META.unknown;
                  const Icon = meta.icon;
                  const isCorrect = s.correct_24h === "correct";
                  const isWrong = s.correct_24h === "incorrect";
                  return (
                    <tr key={s.index} className="border-t border-border/30 hover:bg-muted/20">
                      <td className="py-1.5 px-2 text-right text-muted-foreground font-mono text-xs">{i + 1}</td>
                      <td className="py-1.5 px-2 text-right font-mono text-xs" title={s.date}>{fmtDate(s.date)}</td>
                      <td className="py-1.5 px-2 text-right">
                        <div className="flex items-center gap-1 justify-end">
                          <Icon className={`h-3 w-3 ${meta.color}`} />
                          <span className="text-xs">{meta.label}</span>
                        </div>
                      </td>
                      <td className="py-1.5 px-2 text-left font-mono text-xs">
                        ${s.price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </td>
                      <td className={`py-1.5 px-2 text-left font-mono text-xs ${(s.forward_24h_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {fmtPct(s.forward_24h_pct)}
                      </td>
                      <td className={`py-1.5 px-2 text-left font-mono text-xs ${(s.forward_168h_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {fmtPct(s.forward_168h_pct)}
                      </td>
                      <td className="py-1.5 px-2 text-center">
                        {isCorrect && <CheckCircle2 className="h-4 w-4 text-emerald-400 inline" />}
                        {isWrong && <XCircle className="h-4 w-4 text-rose-400 inline" />}
                        {!isCorrect && !isWrong && <span className="text-muted-foreground">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2 text-xs text-amber-200/90">
            <Info className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <strong>این یک ابزار تحلیل تاریخی است.</strong> {data.note}
              دقت ۲۴h در کل داده: {data.overall_accuracy_24h.accuracy_pct}%.
              در زیرمجموعه‌ی confidence بالا (ADX قوی)، دقت بالاتر است (به صفحه‌ی regime-accuracy مراجعه کنید).
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-xs text-muted-foreground text-center pt-2 space-y-1">
        <p>as_of: <span className="font-mono">{data.as_of}</span></p>
        <Link href="/" className="inline-flex items-center gap-1 mt-2 text-primary hover:underline">
          بازگشت <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
