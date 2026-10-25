"use client";

import { useState } from "react";
import {
  Play,
  Square,
  RotateCcw,
  Zap,
  Loader2,
} from "lucide-react";
import {
  usePaperV3Status,
  useLivePaperV3,
  useStartPaperV3,
  useStopPaperV3,
  useResetPaperV3,
  useBots,
} from "@/lib/queries";
import { getSimulationSymbols } from "@/lib/api";
import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PaperKpiCards } from "@/components/paper-trading/kpi-cards";
import { CheckCountdown } from "@/components/paper-trading/countdown";
import { PaperEventLog } from "@/components/paper-trading/event-log";
import { PaperEquityChart } from "@/components/paper-trading/equity-chart";
import { PaperPositionsCard } from "@/components/paper-trading/positions-card";
import { PaperTradesTable } from "@/components/paper-trading/trades-table";

interface SymbolOption {
  symbol: string;
  name_fa?: string;
  base?: string;
}

interface BotOption {
  slug: string;
  name: string;
  name_en: string;
}

export default function PaperTradingPage() {
  const status = usePaperV3Status();
  const live = useLivePaperV3();
  const startBot = useStartPaperV3();
  const stopBot = useStopPaperV3();
  const resetBot = useResetPaperV3();
  const bots = useBots();

  const [symbols, setSymbols] = useState<SymbolOption[]>([]);
  const [symbol, setSymbol] = useState<string>("ADATMN");
  const [symbolSearch, setSymbolSearch] = useState<string>("");
  const [timeframe, setTimeframe] = useState<string>("1h");
  const [botSlug, setBotSlug] = useState<string>("scalp_master");
  const [initialBalance, setInitialBalance] = useState<number>(1000);
  const [intervalSec, setIntervalSec] = useState<number>(60);

  const data = live.data ?? status.data;
  const isRunning = data?.is_running ?? false;

  const filteredSymbols = symbolSearch.trim()
    ? symbols.filter((s) => {
        const q = symbolSearch.trim().toLowerCase();
        return (
          s.symbol.toLowerCase().includes(q) ||
          (s.name_fa && s.name_fa.includes(symbolSearch.trim())) ||
          (s.base && s.base.toLowerCase().includes(q))
        );
      })
    : symbols;

  useEffect(() => {
    getSimulationSymbols()
      .then((res) => {
        if (res && res.symbols && res.symbols.length > 0) {
          setSymbols(res.symbols);
          // Functional setter: no 'symbol' in deps (prevents re-fetch loop)
          setSymbol((prev) => prev || res.symbols[0].symbol);
        }
      })
      .catch((err) => console.error("Symbols load error:", err));
  }, []);

  const handleStart = () => {
    startBot.mutate({
      bot_slug: botSlug,
      symbols: [symbol],
      timeframe,
      initial_capital: initialBalance,
      check_interval_sec: intervalSec,
      position_size_pct: 50,
    });
  };

  const botOptions = bots.data?.bots ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Zap className="h-6 w-6 text-emerald-400" />
            Paper Trading
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            تست زنده استراتژی‌ها روی داده‌ی واقعی والکس
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <Button
              onClick={handleStart}
              disabled={startBot.isPending || !symbol}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              {startBot.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              شروع
            </Button>
          ) : (
            <Button
              onClick={() => stopBot.mutate()}
              disabled={stopBot.isPending}
              variant="destructive"
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              توقف
            </Button>
          )}
          <Button
            onClick={() => resetBot.mutate()}
            variant="outline"
            size="icon"
            disabled={resetBot.isPending || isRunning}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Status banner */}
      <Card
        className={`border-2 ${isRunning ? "border-emerald-500/40 bg-emerald-500/5" : "border-white/10"}`}
      >
        <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div className="flex items-center gap-3">
            <div
              className={`h-3 w-3 rounded-full ${isRunning ? "animate-pulse bg-emerald-400" : "bg-zinc-500"}`}
            />
            <div>
              <p className="font-semibold">
                {isRunning ? "در حال اجرا" : "متوقف"}
              </p>
              <p className="text-xs text-muted-foreground">
                {isRunning && data
                  ? `چک: ${data.check_count ?? 0} بار | آخرین: ${data.last_check_at ? new Date(data.last_check_at * 1000).toLocaleTimeString("en-GB", { hour12: false }) : "—"}`
                  : "برای شروع، دکمه را بزنید"}
              </p>
            </div>
          </div>

        </CardContent>
      </Card>

      {/* Countdown */}
      {isRunning && (
        <Card className="border-emerald-500/20 bg-emerald-500/5">
          <CardContent className="py-3">
            <CheckCountdown
              lastCheck={data?.last_check_at ?? 0}
              intervalSec={data?.config?.check_interval_sec ?? intervalSec}
              isRunning={isRunning}
            />
          </CardContent>
        </Card>
      )}

      {/* Configuration */}
      {!isRunning && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-5 w-5 text-amber-400" />
              تنظیمات
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {/* ربات */}
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">ربات</label>
                <select
                  value={botSlug}
                  onChange={(e) => setBotSlug(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-sm outline-none focus:border-amber-500"
                >
                  {botOptions.map((b: BotOption) => (
                    <option key={b.slug} value={b.slug} className="bg-slate-900">
                      {b.name} — {b.name_en}
                    </option>
                  ))}
                </select>
              </div>

              {/* نماد */}
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">نماد</label>
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    placeholder="جستجو..."
                    value={symbolSearch}
                    onChange={(e) => setSymbolSearch(e.target.value)}
                    className="w-[100px] bg-black/40 border border-white/10 rounded px-2 py-2 text-sm outline-none focus:border-amber-500"
                  />
                  <select
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    disabled={filteredSymbols.length === 0}
                    className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm outline-none focus:border-amber-500"
                  >
                    {filteredSymbols.length === 0 && (
                      <option value="">نتیجه‌ای یافت نشد</option>
                    )}
                    {filteredSymbols.map((s: SymbolOption) => (
                      <option key={s.symbol} value={s.symbol} className="bg-slate-900">
                        {s.name_fa} ({s.base})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* TF */}
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">تایم‌فریم</label>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-sm outline-none focus:border-amber-500"
                >
                  <option value="15m" className="bg-slate-900">۱۵ دقیقه</option>
                  <option value="1h" className="bg-slate-900">۱ ساعته</option>
                  <option value="4h" className="bg-slate-900">۴ ساعته</option>
                  <option value="1D" className="bg-slate-900">روزانه</option>
                </select>
              </div>

              {/* سرمایه */}
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">سرمایه اولیه (USDT)</label>
                <input
                  type="number"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(Number(e.target.value) || 1000)}
                  min={10}
                  step={100}
                  className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-sm outline-none focus:border-amber-500"
                />
              </div>

              {/* Interval */}
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">فاصله چک (ثانیه)</label>
                <input
                  type="number"
                  value={intervalSec}
                  onChange={(e) => setIntervalSec(Number(e.target.value) || 60)}
                  min={10}
                  step={30}
                  className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-sm outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <PaperKpiCards data={data} isLoading={status.isLoading} />

      {/* Equity Chart */}
      <PaperEquityChart
        data={data?.equity_curve ?? []}
        initialCapital={data?.initial_capital ?? initialBalance}
      />

      {/* Positions + Trades */}
      <div className="grid gap-4 lg:grid-cols-2">
        <PaperPositionsCard positions={data?.open_positions ?? []} />
        <PaperTradesTable trades={data?.recent_trades ?? []} />
      </div>

      {/* Event Log */}
      <PaperEventLog events={data?.events ?? []} radar={data?.radar ?? []} />
    </div>
  );
}
