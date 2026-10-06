"use client";

import { Activity, Clock, TrendingDown, TrendingUp, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Event {
  time: number;
  kind: string;
  message: string;
  symbol: string;
}

interface Props {
  events: Event[];
}

const ICONS: Record<string, React.ElementType> = {
  signal: Zap,
  enter: TrendingUp,
  exit: TrendingDown,
  win: TrendingUp,
  scan: Activity,
};

const COLORS: Record<string, string> = {
  signal: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  enter: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  exit: "text-red-400 bg-red-500/10 border-red-500/20",
  win: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  scan: "text-muted-foreground bg-white/5 border-white/10",
};

export function PaperEventLog({ events }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-400" />
            لاگ زنده
          </span>
          <Badge variant="outline">{events.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <Clock className="mx-auto mb-2 h-6 w-6 opacity-30" />
            هنوز رویدادی ثبت نشده
          </div>
        ) : (
          <div className="max-h-80 space-y-1.5 overflow-y-auto pr-1">
            {events.map((e, i) => {
              const Icon = ICONS[e.kind] ?? Activity;
              const colorClass = COLORS[e.kind] ?? COLORS.scan;
              const time = new Date(e.time * 1000).toLocaleTimeString("fa-IR");
              return (
                <div
                  key={i}
                  className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-[11px] ${colorClass}`}
                >
                  <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <div className="flex-1">
                    <span className="font-mono text-[10px] opacity-70">{time}</span>
                    {e.symbol && (
                      <span className="mr-2 font-mono font-semibold">
                        {e.symbol}
                      </span>
                    )}
                    <span>{e.message}</span>
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
