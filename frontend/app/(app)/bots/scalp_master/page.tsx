"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Zap,
  Play,
  Square,
  RotateCcw,
  Target,
  Plus,
  X,
  TrendingUp,
  Activity,
} from "lucide-react";
import {
  useBot,
  useBotStatus,
  useStartBot,
  useStopBot,
  useResetBot,
  useSetBotSymbols,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const COMMON_SYMBOLS = [
  "SANDTMN", "ORCATMN", "PUMPTMN", "STRKTMN", "TOSHITMN",
  "NMRTMN", "QNTTMN", "EDUTMN", "ONETMN", "NEARTMN",
  "SUITMN", "BONKTMN", "UNITMN", "MOGTMN", "SHIBTMN",
  "DOGETMN", "FILTMN", "ZECTMN", "ADATMN", "SOLTMN",
];

export default function ScalpMasterPage() {
  const slug = "scalp_master";

  const info = useBot(slug);
  const status = useBotStatus(slug);
  const startBot = useStartBot();
  const stopBot = useStopBot();
  const resetBot = useResetBot();
  const setSymbols = useSetBotSymbols();

  type ScalpSignal = { symbol?: string; [k: string]: unknown };
  type ScalpStatus = {
    is_running: boolean;
    paper_mode?: boolean;
    capital?: number;
    started_at: number;
    last_check_at: number;
    check_count: number;
    signals_count: number;
    signals: ScalpSignal[];
    symbols: string[];
    config: { timeframe: string; drop_threshold_pct: number; sl_atr_mult: number; tp_atr_mult: number; check_interval_sec: number };
  };
  const data = status.data as unknown as ScalpStatus | undefined;
  const isRunning = data?.is_running ?? false;
  const currentSymbols: string[] = data?.symbols ?? [];
  const [newSymbol, setNewSymbol] = useState("");

  const addSymbol = () => {
    const sym = newSymbol.trim().toUpperCase();
    if (!sym) return;
    if (currentSymbols.includes(sym)) {
      setNewSymbol("");
      return;
    }
    if (currentSymbols.length >= 2) return;
    setSymbols.mutate({ slug, symbols: [...currentSymbols, sym] });
    setNewSymbol("");
  };

  const removeSymbol = (sym: string) => {
    const next = currentSymbols.filter((s) => s !== sym);
    if (next.length === 0) return;
    setSymbols.mutate({ slug, symbols: next });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <Link
          href="/bots"
          className="flex h-9 w-9 items-center justify-center rounded-lg border transition hover:border-emerald-500/30 hover:bg-emerald-500/5"
        >
          <ArrowRight className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          {info.isLoading ? (
            <Skeleton className="h-8 w-64" />
          ) : info.data ? (
            <>
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/30 to-amber-500/0">
                  <Zap className="h-6 w-6 text-amber-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold tracking-tight">
                    {info.data.name}
                  </h1>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-xs text-muted-foreground">
                      {info.data.name_en} • v{info.data.version}
                    </p>
                    {data?.paper_mode && (
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-[10px]">
                        Paper Mode
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {info.data.description}
              </p>
            </>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <Button
              onClick={() => startBot.mutate(slug)}
              disabled={startBot.isPending || currentSymbols.length === 0}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              <Play className="h-4 w-4" />
              شروع
            </Button>
          ) : (
            <Button
              onClick={() => stopBot.mutate(slug)}
              disabled={stopBot.isPending}
              variant="destructive"
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              توقف
            </Button>
          )}
          <Button
            onClick={() => resetBot.mutate(slug)}
            variant="outline"
            size="icon"
            disabled={resetBot.isPending || isRunning}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-5 w-5 text-amber-400" />
            نمادهای انتخابی (حداکثر ۲)
            <Badge variant="outline">{currentSymbols.length}/2</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {currentSymbols.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                هنوز نمادی انتخاب نشده
              </p>
            ) : (
              currentSymbols.map((sym) => (
                <Badge
                  key={sym}
                  variant="outline"
                  className="gap-1.5 border-amber-500/30 bg-amber-500/5 px-3 py-1.5 text-amber-300"
                >
                  <span className="font-mono">{sym}</span>
                  {!isRunning && (
                    <button
                      onClick={() => removeSymbol(sym)}
                      className="hover:text-red-400"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </Badge>
              ))
            )}
          </div>

          {!isRunning && currentSymbols.length < 2 && (
            <div className="flex items-center gap-2">
              <select
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                className="flex-1 bg-slate-900 border border-white/10 rounded px-3 py-1.5 text-sm text-white outline-none focus:border-amber-500"
              >
                <option value="">انتخاب نماد...</option>
                {COMMON_SYMBOLS.filter((s) => !currentSymbols.includes(s)).map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <Button
                onClick={addSymbol}
                disabled={!newSymbol || setSymbols.isPending}
                size="sm"
                className="gap-1"
              >
                <Plus className="h-3 w-3" />
                افزودن
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {data && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-5 w-5 text-emerald-400" />
              وضعیت اسکن
              <Badge variant="outline" className="mr-auto text-[10px]">
                {data.check_count ?? 0} چک
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">تعداد چک</p>
                <p className="font-mono text-2xl font-bold text-blue-400">
                  {data.check_count ?? 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">سیگنال‌ها</p>
                <p className="font-mono text-2xl font-bold text-amber-400">
                  {data.signals_count ?? 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">آخرین چک</p>
                <p className="font-mono text-sm mt-1.5">
                  {data.last_check_at
                    ? new Date(data.last_check_at * 1000).toLocaleTimeString("en-GB", { hour12: false })
                    : "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">سرمایه مجازی</p>
                <p className="font-mono text-sm font-bold text-emerald-400 mt-1.5">
                  {(data.capital ?? 0).toLocaleString()} TMN
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">دوره اسکن</p>
                <p className="font-mono text-sm mt-1.5">
                  {Math.round((data.config?.check_interval_sec ?? 1800) / 60)} دقیقه
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {data && data.signals && data.signals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-base">
              <span className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-amber-400" />
                سیگنال‌های اخیر
              </span>
              <Badge variant="outline">{data.signals_count}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              {data.signals.map((sig: any, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="font-mono text-xs font-semibold">
                      {sig.symbol}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {sig.reason}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-xs font-bold text-emerald-400">
                      +{sig.drop_pct}%
                    </p>
                    <p className="font-mono text-[10px] text-muted-foreground">
                      RSI={sig.rsi}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {info.data && (
        <Card>
          <CardContent className="space-y-2 pt-6 text-sm">
            <p className="text-muted-foreground">{info.data.description}</p>
            <div className="flex flex-wrap gap-1 pt-2">
              {info.data.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="text-[10px]">
                  #{tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
