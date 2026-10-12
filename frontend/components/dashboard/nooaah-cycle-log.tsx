"use client";

import { useState } from "react";
import {
  Activity,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Clock,
  AlertCircle,
  Zap,
  Loader2,
  Ban,
} from "lucide-react";
import { useNooaahCycles } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ACTION_META: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  opened: {
    icon: <Zap className="h-3.5 w-3.5" />,
    color: "text-emerald-500 border-emerald-500/40 bg-emerald-500/5",
    label: "ورود",
  },
  position_held: {
    icon: <Activity className="h-3.5 w-3.5" />,
    color: "text-sky-500 border-sky-500/40 bg-sky-500/5",
    label: "پوزیشن باز",
  },
  no_signal: {
    icon: <Clock className="h-3.5 w-3.5" />,
    color: "text-muted-foreground border-border/40",
    label: "بدون سیگنال",
  },
  cooldown: {
    icon: <Ban className="h-3.5 w-3.5" />,
    color: "text-amber-500 border-amber-500/40 bg-amber-500/5",
    label: "Cooldown",
  },
  killed: {
    icon: <Ban className="h-3.5 w-3.5" />,
    color: "text-red-500 border-red-500/40 bg-red-500/5",
    label: "متوقف",
  },
  no_capital: {
    icon: <AlertCircle className="h-3.5 w-3.5" />,
    color: "text-red-500 border-red-500/40 bg-red-500/5",
    label: "بدون سرمایه",
  },
  duplicate_symbol: {
    icon: <AlertCircle className="h-3.5 w-3.5" />,
    color: "text-amber-500 border-amber-500/40 bg-amber-500/5",
    label: "نماد تکراری",
  },
  execute_failed: {
    icon: <AlertCircle className="h-3.5 w-3.5" />,
    color: "text-red-500 border-red-500/40 bg-red-500/5",
    label: "خطا",
  },
  bad_price: {
    icon: <AlertCircle className="h-3.5 w-3.5" />,
    color: "text-red-500 border-red-500/40 bg-red-500/5",
    label: "قیمت نامعتبر",
  },
};

const fmtTime = (ts: number) =>
  new Date(ts * 1000).toLocaleTimeString("fa-IR", {
    hour: "2-digit",
    minute: "2-digit",
  });

const fmtDate = (ts: number) =>
  new Date(ts * 1000).toLocaleDateString("fa-IR", {
    month: "short",
    day: "numeric",
  });

export function NooaahCycleLog() {
  const [expanded, setExpanded] = useState(true);
  const cycles = useNooaahCycles(30);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            گزارش چرخه‌ها
            {cycles.data && (
              <span className="text-xs font-normal text-muted-foreground">
                ({cycles.data.length} چرخه)
              </span>
            )}
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted"
            aria-label={expanded ? "بستن" : "باز کردن"}
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </CardTitle>
      </CardHeader>

      {expanded && (
        <CardContent>
          {cycles.isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              در حال بارگذاری...
            </div>
          )}

          {cycles.data && cycles.data.length === 0 && (
            <div className="rounded-lg border border-border/40 bg-muted/30 p-3 text-xs text-muted-foreground">
              هنوز هیچ چرخه‌ای ثبت نشده. بعد از اولین اجرای scheduler (تا ۳۰ دقیقه)، اینجا نمایش داده می‌شه.
            </div>
          )}

          {cycles.data && cycles.data.length > 0 && (
            <div className="max-h-80 space-y-1.5 overflow-y-auto pr-1">
              {cycles.data.map((c, i) => {
                const meta = ACTION_META[c.action] || ACTION_META.no_signal;
                return (
                  <div
                    key={`${c.timestamp}-${i}`}
                    className={`flex items-start gap-2 rounded-lg border p-2.5 text-xs ${meta.color}`}
                  >
                    <span className="mt-0.5 shrink-0">{meta.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold">{meta.label}</span>
                        <span className="shrink-0 font-mono text-[10px] text-muted-foreground" dir="ltr">
                          {fmtDate(c.timestamp)} {fmtTime(c.timestamp)}
                        </span>
                      </div>
                      <div className="mt-1 break-words text-muted-foreground">
                        {c.reason_fa}
                      </div>
                      {c.opened_symbol && (
                        <div className="mt-1 font-mono text-[10px]">
                          <span className="font-bold text-emerald-500">
                            {c.opened_symbol}
                          </span>{" "}
                          {c.opened_confidence && (
                            <span className="text-muted-foreground">
                              conf={c.opened_confidence}٪
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
