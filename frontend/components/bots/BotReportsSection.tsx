"use client";

import Link from "next/link";
import { BarChart3, Activity, Archive, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatPct, formatTime } from "@/lib/format";

type BotReportData = {
  slug: string;
  name?: string;
  name_en?: string;
  description?: string;
  archived?: boolean;
  status?: string;
  backtest?: {
    status: string;
    sources?: Record<string, unknown>;
  };
  paper?: {
    status: string;
    mode?: string;
    regime?: string;
    active_bots?: string[];
    capital_total?: number;
    capital_available?: number;
    cash?: number;
    open_positions?: number;
    closed_trades?: number;
    daily_pnl_pct?: number;
    killed?: boolean;
    kill_switch_manual?: boolean;
    kill_switch_auto?: boolean;
    gate?: { allow_new_entries?: boolean; updated_at?: string };
    source?: string;
    note?: string;
  };
  meta?: {
    status: string;
    archived?: boolean;
    tags?: string[];
    capabilities?: string[];
    tier?: string;
  };
};

export function BotReportsSection({ data }: { data: BotReportData }) {
  const archived = Boolean(data.meta?.archived || data.archived);
  const backtest = data.backtest ?? { status: "no_data" };
  const paper = data.paper ?? { status: "no_data" };

  return (
    <div className="space-y-4 mt-6">
      {archived && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="py-3 flex items-center gap-2 text-sm text-amber-300">
            <Archive className="h-4 w-4" />
            این ربات آرشیو شده است. آمار backtest فقط برای مرجع نمایش داده می‌شود.
          </CardContent>
        </Card>
      )}

      {/* Backtest */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-4 w-4" /> Backtest
          </CardTitle>
        </CardHeader>
        <CardContent>
          {backtest.status !== "ok" ? (
            <p className="text-sm text-muted-foreground">
              داده‌ی backtest برای این ربات موجود نیست.
            </p>
          ) : (
            <BacktestTable sources={backtest.sources ?? {}} />
          )}
        </CardContent>
      </Card>

      {/* Paper */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <Activity className="h-4 w-4" /> Paper
            </span>
            {data.slug === "sarv_router" && (
              <Link
                href="/sarvrouter"
                className="text-xs text-primary hover:underline flex items-center gap-1"
              >
                وضعیت زنده <ExternalLink className="h-3 w-3" />
              </Link>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {paper.status === "archived" ? (
            <p className="text-sm text-muted-foreground">
              {paper.note ?? "این ربات آرشیو شده است."}
            </p>
          ) : paper.status !== "ok" ? (
            <p className="text-sm text-muted-foreground">
              داده‌ی paper برای این ربات موجود نیست.{" "}
              <Link href="/paper-trading" className="text-primary hover:underline">
                مشاهده Paper Mode
              </Link>
            </p>
          ) : (
            <PaperStats paper={paper} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PaperStats({ paper }: { paper: NonNullable<BotReportData["paper"]> }) {
  const rows: Array<[string, string]> = [];
  if (paper.mode) rows.push(["حالت", paper.mode]);
  if (paper.regime) rows.push(["رژیم", paper.regime]);
  if (typeof paper.capital_total === "number")
    rows.push(["سرمایه کل", formatNumber(paper.capital_total)]);
  if (typeof paper.capital_available === "number")
    rows.push(["سرمایه آزاد", formatNumber(paper.capital_available)]);
  if (typeof paper.cash === "number")
    rows.push(["Cash", formatNumber(paper.cash)]);
  if (typeof paper.open_positions === "number")
    rows.push(["پوزیشن باز", String(paper.open_positions)]);
  if (typeof paper.closed_trades === "number")
    rows.push(["ترید بسته", String(paper.closed_trades)]);
  if (typeof paper.daily_pnl_pct === "number")
    rows.push(["PnL امروز", formatPct(paper.daily_pnl_pct)]);
  if (paper.gate?.updated_at)
    rows.push(["آخرین gate", formatTime(new Date(paper.gate.updated_at).getTime() / 1000)]);
  if (paper.gate && typeof paper.gate.allow_new_entries === "boolean")
    rows.push(["ورود جدید", paper.gate.allow_new_entries ? "مجاز" : "مسدود"]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {rows.map(([k, v]) => (
        <div key={k}>
          <p className="text-xs text-muted-foreground">{k}</p>
          <p className="text-sm font-medium">{v}</p>
        </div>
      ))}
      {(paper.kill_switch_manual || paper.kill_switch_auto || paper.killed) && (
        <div className="col-span-full">
          <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/30">
            Kill switch فعال
          </Badge>
        </div>
      )}
    </div>
  );
}

function BacktestTable({ sources }: { sources: Record<string, unknown> }) {
  // Flatten periods from any source that has {periods: {...}}
  type Row = { label: string; trades?: number; wr?: number; pf?: number; pnl?: number; dd?: number };
  const rows: Row[] = [];

  for (const [, val] of Object.entries(sources)) {
    if (!val || typeof val !== "object") continue;
    const v = val as Record<string, unknown>;
    const periods = (v.periods ?? v) as Record<string, unknown>;
    if (!periods || typeof periods !== "object") continue;
    for (const [label, p] of Object.entries(periods)) {
      if (!p || typeof p !== "object") continue;
      const pp = p as Record<string, unknown>;
      if (typeof pp.trades !== "number") continue;
      rows.push({
        label,
        trades: pp.trades as number,
        wr: (pp.win_rate_pct ?? pp.win_rate) as number | undefined,
        pf: pp.pf as number | undefined,
        pnl: pp.pnl_pct as number | undefined,
        dd: pp.dd_pct as number | undefined,
      });
    }
    if (rows.length) break; // first source with periods wins
  }

  if (!rows.length) {
    return (
      <p className="text-sm text-muted-foreground">
        داده‌ی قابل‌نمایش در backtest موجود نیست.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-xs text-muted-foreground">
            <th className="text-right py-2 px-2">دوره</th>
            <th className="text-right py-2 px-2">ترید</th>
            <th className="text-right py-2 px-2">Win%</th>
            <th className="text-right py-2 px-2">PF</th>
            <th className="text-right py-2 px-2">PnL%</th>
            <th className="text-right py-2 px-2">DD%</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-b border-border/40">
              <td className="py-2 px-2 font-medium">{r.label}</td>
              <td className="py-2 px-2">{r.trades ?? "—"}</td>
              <td className="py-2 px-2">
                {r.wr != null ? `${r.wr.toFixed(1)}%` : "—"}
              </td>
              <td className="py-2 px-2">
                {r.pf != null ? r.pf.toFixed(2) : "—"}
              </td>
              <td
                className={
                  "py-2 px-2 " +
                  (r.pnl == null
                    ? ""
                    : r.pnl >= 0
                    ? "text-emerald-400"
                    : "text-rose-400")
                }
              >
                {r.pnl != null ? formatPct(r.pnl) : "—"}
              </td>
              <td className="py-2 px-2">
                {r.dd != null ? `${r.dd.toFixed(1)}%` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
