"use client";

import { useEffect, useMemo, useRef } from "react";
import { AlertTriangle, Brain, Check, Clock, Target, TrendingDown, TrendingUp, X, Zap, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Check_ {
  name: string;
  label: string;
  passed: boolean;
  value: number | string | null;
  threshold: number | string | null;
}

interface Ev {
  time: number;
  kind: string;
  message: string;
  symbol?: string;
  data?: { checks?: Check_[]; decision?: string } & Record<string, unknown>;
}

interface RadarItem {
  symbol: string;
  passed: number;
  total: number;
  pct: number;
  checks?: Check_[];
}

interface Props {
  events: Ev[];
  radar?: RadarItem[];
}

const STYLE: Record<string, { icon: React.ElementType; cls: string }> = {
  think: { icon: Brain, cls: "border-violet-500/25 bg-violet-500/[0.06] text-violet-700 dark:text-violet-300" },
  scan: { icon: Activity, cls: "border-zinc-500/20 bg-zinc-500/[0.05] text-muted-foreground" },
  signal: { icon: Zap, cls: "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300" },
  enter: { icon: TrendingUp, cls: "border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300" },
  exit: { icon: TrendingDown, cls: "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300" },
  win: { icon: TrendingUp, cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" },
  error: { icon: AlertTriangle, cls: "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400" },
};

const fmt = (v: number | string | null | undefined) =>
  v === null || v === undefined ? "" : typeof v === "number" ? String(v) : v;

function CheckChips({ checks }: { checks: Check_[] }) {
  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {checks.map((c) => (
        <span
          key={c.name}
          className={
            "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] " +
            (c.passed
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
              : "border-red-500/25 bg-red-500/[0.07] text-red-700 dark:text-red-300")
          }
        >
          {c.passed ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
          {c.label}
          {c.value !== null && c.value !== undefined && (
            <span className="font-mono opacity-80" dir="ltr">
              {fmt(c.value)}
              {c.threshold !== null && c.threshold !== undefined ? " / " + fmt(c.threshold) : ""}
            </span>
          )}
        </span>
      ))}
    </div>
  );
}

function Radar({ items }: { items: RadarItem[] }) {
  if (!items.length) return null;
  return (
    <div className="mb-4 space-y-2 rounded-xl border border-border/60 p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Target className="h-4 w-4 text-violet-500" />
        رادار کاندیدها: فاصله تا شرط ورود
      </div>
      {items.map((r) => {
        const ready = r.total > 0 && r.passed === r.total;
        return (
          <div key={r.symbol} className="space-y-1">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-mono font-semibold">{r.symbol}</span>
              <span className={"tabular-nums " + (ready ? "font-bold text-emerald-500" : "text-muted-foreground")}>
                {r.passed.toLocaleString("en-US")} از {r.total.toLocaleString("en-US")} شرط · {r.pct.toLocaleString("en-US")}٪
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-300/50 dark:bg-zinc-800/70">
              <div
                className={
                  "h-full rounded-full transition-all duration-700 " +
                  (ready
                    ? "bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.8)]"
                    : r.pct >= 60
                    ? "bg-amber-400"
                    : "bg-violet-400/70")
                }
                style={{ width: r.pct + "%", marginLeft: "auto" }}
              />
            </div>
            {r.checks && r.checks.length > 0 && <CheckChips checks={r.checks} />}
          </div>
        );
      })}
    </div>
  );
}

export function PaperEventLog({ events, radar = [] }: Props) {
  const keyed = useMemo(() => {
    const cnt = new Map<string, number>();
    return events.slice(0, 60).map((e) => {
      const base = e.time + "-" + e.kind + "-" + (e.symbol ?? "") + "-" + e.message;
      const n = cnt.get(base) ?? 0;
      cnt.set(base, n + 1);
      return { e, key: base + "#" + n };
    });
  }, [events]);

  // رویدادهای موجود هنگام اولین رندر انیمیشن نمی‌گیرند؛ فقط رویدادهای تازه.
  const seen = useRef<Set<string> | null>(null);
  if (seen.current === null) seen.current = new Set(keyed.map((k) => k.key));
  const fresh = new Set(keyed.filter((k) => !seen.current!.has(k.key)).map((k) => k.key));
  useEffect(() => {
    keyed.forEach((k) => seen.current!.add(k.key));
  }, [keyed]);

  const lastScan = events.find((e) => e.kind === "scan");

  return (
    <Card>
      <style>{`
        @keyframes brain-in {
          0%   { opacity: 0; transform: translateY(-14px) scale(0.98); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-violet-500" />
            مغز ربات
          </span>
          <Badge variant="outline">{events.length}</Badge>
        </CardTitle>
        {lastScan && (
          <p className="text-xs text-muted-foreground">آخرین اسکن: {lastScan.message}</p>
        )}
      </CardHeader>
      <CardContent>
        <Radar items={radar} />

        {keyed.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
            ربات هنوز چیزی ندیده؛ منتظر اولین چک…
          </div>
        ) : (
          <div className="max-h-96 space-y-1.5 overflow-y-auto pr-1">
            {keyed.map(({ e, key }) => {
              const st = STYLE[e.kind] ?? STYLE.scan;
              const Icon = st.icon;
              const time = new Date(e.time * 1000).toLocaleTimeString("en-GB", { hour12: false });
              const checks = e.data?.checks;
              const decision = e.data?.decision;
              return (
                <div
                  key={key}
                  className={"flex items-start gap-2 rounded-lg border px-3 py-2 text-[11px] " + st.cls}
                  style={fresh.has(key) ? { animation: "brain-in 0.45s ease-out" } : undefined}
                >
                  <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-x-2">
                      <span className="font-mono text-[10px] opacity-70">{time}</span>
                      {e.symbol && <span className="font-mono font-semibold">{e.symbol}</span>}
                      <span>{e.message}</span>
                      {decision && (
                        <Badge variant="outline" className="text-[9px]">
                          {decision === "enter" ? "ورود" : "رد شد"}
                        </Badge>
                      )}
                    </div>
                    {checks && checks.length > 0 && <CheckChips checks={checks} />}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
