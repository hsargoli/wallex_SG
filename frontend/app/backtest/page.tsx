"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, FlaskConical, Loader2, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getSimulationSymbols, runBotBacktest, type BotBacktestResult } from "@/lib/api";

const REASONS: Record<string, string> = {
  take_profit: "حد سود",
  stop_loss: "حد ضرر",
  timeout: "پایان زمان",
  end_of_data: "پایان داده",
};

const pnlColor = (v: number) =>
  v > 0 ? "text-emerald-500" : v < 0 ? "text-red-500" : "text-muted-foreground";

const fmtDate = (t: number) =>
  new Date(t * 1000).toLocaleDateString("fa-IR", { month: "short", day: "numeric" });

type SortKey = "symbol" | "trades" | "win_rate" | "pnl_pct" | "max_drawdown_pct";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted-foreground">
      {label}
      {children}
    </label>
  );
}

const inputCls =
  "h-9 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/40";

function Histogram({ values }: { values: number[] }) {
  const bins = useMemo(() => {
    if (!values.length) return [];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const n = 12;
    const step = (max - min) / n || 1;
    const arr = Array.from({ length: n }, (_, i) => ({ from: min + i * step, count: 0 }));
    values.forEach((v) => {
      const idx = Math.min(n - 1, Math.floor((v - min) / step));
      arr[idx].count += 1;
    });
    return arr;
  }, [values]);
  const peak = Math.max(1, ...bins.map((b) => b.count));
  return (
    <div dir="ltr" className="flex h-32 items-end gap-1">
      {bins.map((b, i) => (
        <div key={i} className="flex flex-1 flex-col items-center gap-1">
          <div
            className={"w-full rounded-t " + (b.from + 0.0001 >= 0 ? "bg-emerald-500/70" : "bg-red-500/70")}
            style={{ height: (b.count / peak) * 100 + "%", minHeight: b.count ? 3 : 0 }}
            title={b.count + " ترید"}
          />
          <span className="text-[9px] text-muted-foreground">{b.from.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
}

export default function BacktestPage() {
  const [tf, setTf] = useState("1h");
  const [picked, setPicked] = useState<string[]>(["NEARTMN"]);
  const [q, setQ] = useState("");
  const symbolsQ = useQuery({ queryKey: ["sim-symbols"], queryFn: getSimulationSymbols, staleTime: 300_000 });
  const matches = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t) return [];
    return (symbolsQ.data?.symbols ?? [])
      .filter((o) => !picked.includes(o.symbol) &&
        (o.symbol.toLowerCase().includes(t) || o.base.toLowerCase().includes(t) ||
         (o.name_fa ?? "").includes(q.trim()) || (o.name_en ?? "").toLowerCase().includes(t)))
      .slice(0, 8);
  }, [symbolsQ.data, q, picked]);
  const [capital, setCapital] = useState(1000);
  const [sizePct, setSizePct] = useState(50);
  const [fee, setFee] = useState(0.2);
  const [sortKey, setSortKey] = useState<SortKey>("pnl_pct");
  const [asc, setAsc] = useState(false);

  const m = useMutation<BotBacktestResult, Error>({
    mutationFn: () =>
      runBotBacktest("scalp_master", {
        tf,
        top: picked.length,
        symbols: picked.join(","),
        initial_capital: capital,
        position_size_pct: sizePct,
        fee_pct: fee,
      }),
  });

  const d = m.data;
  const rows = useMemo(() => {
    if (!d) return [];
    const r = [...d.per_symbol];
    r.sort((a, b) => {
      const x = a[sortKey];
      const y = b[sortKey];
      const c = typeof x === "string" ? x.localeCompare(y as string) : (x as number) - (y as number);
      return asc ? c : -c;
    });
    return r;
  }, [d, sortKey, asc]);

  const setSort = (k: SortKey) => {
    if (k === sortKey) setAsc(!asc);
    else {
      setSortKey(k);
      setAsc(false);
    }
  };

  const th = (k: SortKey, label: string) => (
    <th className="cursor-pointer px-3 py-2 text-right font-medium hover:text-foreground" onClick={() => setSort(k)}>
      {label}
      {sortKey === k ? (asc ? " ▲" : " ▼") : ""}
    </th>
  );

  return (
    <div className="mx-auto max-w-5xl space-y-5 p-4" dir="rtl">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          بک‌تست <FlaskConical className="h-5 w-5 text-emerald-500" />
        </h1>
        <p className="text-sm text-muted-foreground">
          بازپخش ربات Scalp Master روی کندل‌های گذشته (بدون نگاه به آینده، با کارمزد)
        </p>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-end gap-4 pt-6">
          <Field label="تایم‌فریم">
            <select className={inputCls} value={tf} onChange={(e) => setTf(e.target.value)}>
              <option value="15m">۱۵ دقیقه</option>
              <option value="1h">۱ ساعت</option>
              <option value="4h">۴ ساعت</option>
            </select>
          </Field>
          <div className="w-full space-y-2">
            <div className="text-xs text-muted-foreground">
              رمزارزها ({picked.length} از ۵) — حداقل ۱ و حداکثر ۵
            </div>
            <div className="flex flex-wrap gap-2">
              {picked.map((s) => (
                <span key={s} className="flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-mono text-xs">
                  {s}
                  <button type="button" onClick={() => setPicked(picked.filter((x) => x !== s))}
                    className="text-muted-foreground hover:text-red-500" aria-label="حذف">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="relative">
              <input className={inputCls + " w-full"} dir="ltr" value={q}
                disabled={picked.length >= 5}
                placeholder={picked.length >= 5 ? "به سقف ۵ نماد رسیدی" : "جست‌وجو: BTC، ETH، بیت‌کوین…"}
                onChange={(e) => setQ(e.target.value)} />
              {q.trim() && picked.length < 5 && (
                <div className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-border bg-popover shadow-lg">
                  {matches.length === 0 && <div className="p-3 text-xs text-muted-foreground">نمادی پیدا نشد</div>}
                  {matches.map((o) => (
                    <button key={o.symbol} type="button"
                      className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-accent"
                      onClick={() => { setPicked([...picked, o.symbol]); setQ(""); }}>
                      <span className="font-mono" dir="ltr">{o.symbol}</span>
                      <span className="text-xs text-muted-foreground">{o.name_fa}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <Field label="سرمایه‌ی هر نماد">
            <input className={inputCls + " w-28"} type="number" min={10} value={capital}
              onChange={(e) => setCapital(Number(e.target.value))} />
          </Field>
          <Field label="درصد هر پوزیشن">
            <input className={inputCls + " w-24"} type="number" min={1} max={100} value={sizePct}
              onChange={(e) => setSizePct(Number(e.target.value))} />
          </Field>
          <Field label="کارمزد ٪">
            <input className={inputCls + " w-24"} type="number" step={0.05} min={0} value={fee}
              onChange={(e) => setFee(Number(e.target.value))} />
          </Field>
          <Button onClick={() => m.mutate()} disabled={m.isPending || picked.length === 0} className="h-9">
            {m.isPending ? <Loader2 className="ml-2 h-4 w-4 animate-spin" /> : null}
            {m.isPending ? "در حال بازپخش…" : "اجرای بک‌تست"}
          </Button>
        </CardContent>
      </Card>

      {m.isPending && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 text-center text-sm">
          <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin text-emerald-500" />
          ربات دارد ماه گذشته را روی {picked.length} نماد دوباره زندگی می‌کند… (حدود ۱۰ تا ۲۰ ثانیه)
        </div>
      )}

      {m.isError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-500">
          خطا: {m.error.message}
        </div>
      )}

      {d && (
        <>
          {!d.summary.reliable && (
            <div className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-600">
              <AlertTriangle className="h-4 w-4" />
              نمونه ناکافی است (کمتر از ۳۰ ترید). به این آمار تکیه نکنید.
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              { l: "تعداد ترید", v: String(d.summary.total_trades), c: "" },
              { l: "Win Rate", v: d.summary.win_rate + "٪", c: d.summary.win_rate >= 50 ? "text-emerald-500" : "text-amber-500" },
              { l: "Profit Factor", v: d.summary.profit_factor == null ? "—" : String(d.summary.profit_factor),
                c: (d.summary.profit_factor ?? 0) >= 1 ? "text-emerald-500" : "text-red-500" },
              { l: "میانگین هر ترید", v: d.summary.avg_trade_pct + "٪", c: pnlColor(d.summary.avg_trade_pct) },
            ].map((k) => (
              <Card key={k.l}>
                <CardContent className="pt-5">
                  <div className="text-xs text-muted-foreground">{k.l}</div>
                  <div className={"mt-1 text-2xl font-bold tabular-nums " + k.c} dir="ltr">{k.v}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          <p className="text-xs text-muted-foreground">
            {d.symbols_ok} از {d.symbols_requested} نماد
            {d.symbols_source === "fallback_list" ? " (لیست ثابت، نه بر اساس حجم)" : ""} · میانگین سود هر نماد{" "}
            <span className={pnlColor(d.summary.avg_symbol_pnl_pct)} dir="ltr">{d.summary.avg_symbol_pnl_pct}٪</span>{" "}
            · بدترین افت {d.summary.worst_symbol_dd_pct}٪
          </p>

          <Card>
            <CardHeader><CardTitle className="text-base">مقایسه‌ی نمادها</CardTitle></CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    {th("symbol", "نماد")}
                    {th("trades", "ترید")}
                    {th("win_rate", "Win Rate")}
                    {th("pnl_pct", "سود ٪")}
                    {th("max_drawdown_pct", "افت ٪")}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.symbol} className="border-t border-border/50">
                      <td className="px-3 py-2 font-mono font-semibold">
                        {r.symbol}
                        {r.trades < 5 && <Badge variant="outline" className="mr-2 text-[10px]">کم‌اعتبار</Badge>}
                      </td>
                      <td className="px-3 py-2 tabular-nums">{r.trades}</td>
                      <td className="px-3 py-2 tabular-nums">{r.trades ? r.win_rate + "٪" : "—"}</td>
                      <td className={"px-3 py-2 font-semibold tabular-nums " + pnlColor(r.pnl_pct)} dir="ltr">
                        {r.pnl_pct > 0 ? "+" : ""}{r.pnl_pct}
                      </td>
                      <td className="px-3 py-2 tabular-nums">{r.max_drawdown_pct}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">توزیع سود/زیان تریدها (٪)</CardTitle></CardHeader>
            <CardContent><Histogram values={d.trades.map((t) => t.pnl_pct)} /></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">آخرین تریدها</CardTitle></CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 text-right">نماد</th>
                    <th className="px-3 py-2 text-right">ورود</th>
                    <th className="px-3 py-2 text-right">مدت (کندل)</th>
                    <th className="px-3 py-2 text-right">خروج</th>
                    <th className="px-3 py-2 text-right">سود ٪</th>
                  </tr>
                </thead>
                <tbody>
                  {[...d.trades].reverse().slice(0, 30).map((t, i) => (
                    <tr key={i} className="border-t border-border/50">
                      <td className="px-3 py-1.5 font-mono">{t.symbol}</td>
                      <td className="px-3 py-1.5">{fmtDate(t.entry_time)}</td>
                      <td className="px-3 py-1.5 tabular-nums">{t.duration_candles}</td>
                      <td className="px-3 py-1.5">{REASONS[t.exit_reason] ?? t.exit_reason}</td>
                      <td className={"px-3 py-1.5 font-semibold tabular-nums " + pnlColor(t.pnl_pct)} dir="ltr">
                        {t.pnl_pct > 0 ? "+" : ""}{t.pnl_pct}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
