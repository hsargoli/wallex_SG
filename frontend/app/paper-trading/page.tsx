"use client";

import { useState, useEffect } from "react";
import {
  Play,
  Square,
  RotateCcw,
  Zap,
  Sparkles,
  Calendar,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  usePaperV2Status,
  useStartPaperV2,
  useStopPaperV2,
  useResetPaperV2,
} from "@/lib/queries";
import { runSimulation, getSimulationAvailableDates, getSimulationBots, getSimulationSymbols, compareAllBots, SimulationResult, DateItem, BotOption, SymbolOption, CompareResponse, CompareResultItem } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function PaperTradingPage() {
  const status = usePaperV2Status();
  const startBot = useStartPaperV2();
  const stopBot = useStopPaperV2();
  const resetBot = useResetPaperV2();

  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [availableDates, setAvailableDates] = useState<DateItem[]>([]);
  // ‌preset بازه‌ی زمانی (روز) — همه ربات‌ها روی 1h اجرا میشن
  const [rangeDays, setRangeDays] = useState<number>(10);

  const rangeOptions = [
    { value: 10, label: "۱۰ روز گذشته" },
    { value: 20, label: "۲۰ روز گذشته" },
    { value: 30, label: "۱ ماه گذشته" },
  ];
  // ربات‌های قابل شبیه‌سازی
  const [bots, setBots] = useState<BotOption[]>([]);
  // slug ربات انتخاب‌شده. "" = استراتژی پیش‌فرض
  const [botSlug, setBotSlug] = useState<string>("trend_follow");
  // نمادهای قابل انتخاب
  const [symbols, setSymbols] = useState<SymbolOption[]>([]);
  const [symbol, setSymbol] = useState<string>("BTCUSDT");
  // مقایسه ربات‌ها
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  // سرمایه اولیه
  const [initialBalance, setInitialBalance] = useState<number>(1000);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSimulationAvailableDates(90)
      .then((dates) => {
        if (dates && dates.length > 0) {
          setAvailableDates(dates);
        }
      })
      .catch((err) => console.error("Available dates load error:", err));

    getSimulationBots()
      .then((res) => {
        if (res && res.bots && res.bots.length > 0) {
          setBots(res.bots);
          setBotSlug(res.bots[0].slug);
        }
      })
      .catch((err) => console.error("Bots load error:", err));

    getSimulationSymbols()
      .then((res) => {
        if (res && res.symbols && res.symbols.length > 0) {
          setSymbols(res.symbols);
          setSymbol(res.symbols[0].symbol);
        }
      })
      .catch((err) => console.error("Symbols load error:", err));
  }, []);

  // اگه ربات عوض شد و rangeDays فعلی تو گزینه‌های جدید نبود، ریست کن
  useEffect(() => {
    const validValues = rangeOptions.map((o) => o.value);
    if (!validValues.includes(rangeDays)) {
      setRangeDays(validValues[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [botSlug]);

  // وقتی ورودی‌ها عوض میشن، نتایج قبلی رو پاک کن (تا کاربر گمراه نشه)
  useEffect(() => {
    setSimResult(null);
    setCompareResult(null);
    setError(null);
  }, [symbol, botSlug, rangeDays, initialBalance]);

  const handleRunSimulation = async () => {
    try {
      setError(null);
      setSimLoading(true);

      // end = آخرین تاریخ موجود، start = N روز قبل از آن
      if (availableDates.length === 0) {
        throw new Error("لیست تاریخ‌ها بارگذاری نشده");
      }

      const endItem = availableDates[0];                          // آخرین روز
      const startIdx = Math.min(rangeDays - 1, availableDates.length - 1);
      const startItem = availableDates[startIdx];

      const res = await runSimulation(startItem.gregorian, endItem.gregorian, symbol, botSlug, initialBalance);
      setSimResult(res);
    } catch (err) {
      setError("خطا در اجرای شبیه ساز. لطفا اتصال بک اند را بررسی کنید.");
      console.error(err);
    } finally {
      setSimLoading(false);
    }
  };

  const handleCompare = async () => {
    try {
      setError(null);
      setCompareLoading(true);
      setCompareResult(null);

      if (availableDates.length === 0) {
        throw new Error("لیست تاریخ‌ها بارگذاری نشده");
      }

      const endItem = availableDates[0];
      const startIdx = Math.min(rangeDays - 1, availableDates.length - 1);
      const startItem = availableDates[startIdx];

      const res = await compareAllBots(startItem.gregorian, endItem.gregorian, symbol, initialBalance);
      setCompareResult(res);
    } catch (err) {
      setError("خطا در مقایسه ربات‌ها. لطفا اتصال بک اند را بررسی کنید.");
      console.error(err);
    } finally {
      setCompareLoading(false);
    }
  };

  const data = status.data;
  const isRunning = data?.is_running ?? false;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Zap className="h-6 w-6 text-emerald-400" />
            Paper Trading & Simulator
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            تست زنده استراتژی و شبیه سازی گذشته بازار
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <Button onClick={() => startBot.mutate()} disabled={startBot.isPending} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              <Play className="h-4 w-4" /> شروع
            </Button>
          ) : (
            <Button onClick={() => stopBot.mutate()} disabled={stopBot.isPending} variant="destructive">
              <Square className="h-4 w-4" /> توقف
            </Button>
          )}
          <Button onClick={() => resetBot.mutate()} variant="outline" size="icon" disabled={resetBot.isPending || isRunning}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-5 w-5 text-amber-400" />
            موتور شبیه سازی (ماشین زمان)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground flex items-center gap-1">
                سرمایه اولیه (USDT)
              </label>
              <input
                type="number"
                value={initialBalance}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  setInitialBalance(Number.isFinite(v) && v > 0 ? v : 1000);
                }}
                min={10}
                step={100}
                className="bg-black/40 border border-white/10 rounded px-3 py-1.5 text-sm outline-none focus:border-amber-500 min-w-[140px]"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground flex items-center gap-1">
                <Zap className="h-3 w-3" /> رمزارز
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={symbols.length === 0}
                className="bg-black/40 border border-white/10 rounded px-3 py-1.5 text-sm outline-none focus:border-amber-500 min-w-[180px]"
              >
                {symbols.length === 0 && (
                  <option value="" className="bg-slate-900">در حال بارگذاری...</option>
                )}
                {symbols.map((s) => (
                  <option key={s.symbol} value={s.symbol} className="bg-slate-900">
                    {s.name_fa} ({s.base})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> ربات
              </label>
              <select
                value={botSlug}
                onChange={(e) => setBotSlug(e.target.value)}
                disabled={bots.length === 0}
                className="bg-black/40 border border-white/10 rounded px-3 py-1.5 text-sm outline-none focus:border-amber-500 min-w-[180px]"
              >
                {bots.length === 0 && (
                  <option value="" className="bg-slate-900">در حال بارگذاری...</option>
                )}
                {bots.map((b) => (
                  <option key={b.slug} value={b.slug} className="bg-slate-900">
                    {b.name} — {b.name_en}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" /> بازه‌ی زمانی
              </label>
              <select
                value={rangeDays}
                onChange={(e) => setRangeDays(Number(e.target.value))}
                className="bg-black/40 border border-white/10 rounded px-3 py-1.5 text-sm outline-none focus:border-amber-500 min-w-[180px]"
              >
                {rangeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value} className="bg-slate-900">
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <Button
              onClick={handleRunSimulation}
              disabled={simLoading || availableDates.length === 0}
              className="bg-amber-600 hover:bg-amber-700 text-white min-w-[140px]"
            >
              {simLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "اجرای شبیه سازی"}
            </Button>
            <button
              onClick={handleCompare}
              disabled={compareLoading || availableDates.length === 0}
              className="inline-flex items-center justify-center gap-2 rounded-md border border-amber-500/40 text-amber-300 hover:bg-amber-500/10 px-4 py-2 text-sm font-medium min-w-[140px] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {compareLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "مقایسه همه ربات‌ها"}
            </button>
          </div>

          {/* توضیحات ربات انتخاب‌شده */}
          {(() => {
            const selected = bots.find((b) => b.slug === botSlug);
            if (!selected) return null;
            return (
              <div className="mt-1 space-y-2">
                <div className="text-xs text-muted-foreground border-r-2 border-amber-500/40 pr-3 leading-relaxed">
                  {selected.description}
                  {selected.tags.length > 0 && (
                    <span className="mr-2 text-[10px] text-amber-400/70">
                      {selected.tags.map((t) => `#${t}`).join(" ")}
                    </span>
                  )}
                </div>
                {selected.experimental && selected.warning && (
                  <div className="flex items-start gap-2 text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded p-2 leading-relaxed">
                    <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-400" />
                    <span>{selected.warning}</span>
                  </div>
                )}
              </div>
            );
          })()}

          {error && (
            <Alert className="bg-red-500/10 border-red-500/50">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {simResult && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="p-3 rounded-lg bg-black/30 border border-white/5">
                <p className="text-[10px] uppercase text-muted-foreground">وضعیت</p>
                <p className="text-lg font-mono font-bold text-emerald-400">{simResult.status}</p>
              </div>
              <div className="p-3 rounded-lg bg-black/30 border border-white/5">
                <p className="text-[10px] uppercase text-muted-foreground">موجودی نهایی</p>
                <p className="text-lg font-mono font-bold">{formatNumber(simResult.pnl_report.final_balance)} USDT</p>
              </div>
              <div className="p-3 rounded-lg bg-black/30 border border-white/5">
                <p className="text-[10px] uppercase text-muted-foreground">سود/زیان کل</p>
                <p className={cn("text-lg font-mono font-bold", simResult.pnl_report.total_pnl >= 0 ? "text-emerald-400" : "text-red-400")}>
                  {simResult.pnl_report.total_pnl > 0 ? "+" : ""}{formatNumber(simResult.pnl_report.total_pnl)} USDT
                </p>
              </div>
            </div>
          )}

          {/* جدول مقایسه */}
          {compareResult && (
            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-400" />
                  مقایسه ربات‌ها — {compareResult.symbol}
                </h3>
                <span className="text-[10px] text-muted-foreground">
                  {compareResult.dates.start.jalali_pretty} تا {compareResult.dates.end.jalali_pretty}
                </span>
              </div>
              <div className="overflow-hidden rounded-lg border border-white/10">
                <table className="w-full text-sm">
                  <thead className="bg-black/40 text-muted-foreground text-xs">
                    <tr>
                      <th className="px-3 py-2 text-right">رتبه</th>
                      <th className="px-3 py-2 text-right">ربات</th>
                      <th className="px-3 py-2 text-center">معاملات</th>
                      <th className="px-3 py-2 text-center">نرخ برد</th>
                      <th className="px-3 py-2 text-center">سود/زیان</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareResult.results.map((r, idx) => {
                      const isWinner = idx === 0 && r.status === "success" && r.pnl_pct > 0;
                      return (
                        <tr
                          key={r.bot_slug}
                          className={cn(
                            "border-t border-white/5",
                            isWinner && "bg-emerald-500/5"
                          )}
                        >
                          <td className="px-3 py-2 text-right font-mono text-xs">
                            {isWinner ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : `${idx + 1}`}
                          </td>
                          <td className="px-3 py-2 text-right">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{r.bot_name}</span>
                              {r.experimental && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                                  آزمایشی
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2 text-center font-mono text-xs">
                            {r.status === "success" ? r.total_trades : "—"}
                          </td>
                          <td className="px-3 py-2 text-center font-mono text-xs">
                            {r.status === "success" ? `${r.win_rate}%` : "—"}
                          </td>
                          <td className={cn(
                            "px-3 py-2 text-center font-mono text-sm font-bold",
                            r.status !== "success" ? "text-muted-foreground"
                              : r.pnl_pct > 0 ? "text-emerald-400"
                              : r.pnl_pct < 0 ? "text-red-400"
                              : "text-muted-foreground"
                          )}>
                            {r.status === "success"
                              ? `${r.pnl_pct > 0 ? "+" : ""}${r.pnl_pct.toFixed(2)}%`
                              : "خطا"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {compareResult.results[0]?.status === "success" && compareResult.results[0].pnl_pct > 0 && (
                <p className="text-xs text-emerald-400/80 text-center">
                  ✅ بهترین ربات: <span className="font-bold">{compareResult.results[0].bot_name}</span>
                  {" "}با بازده {compareResult.results[0].pnl_pct.toFixed(2)}%
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
