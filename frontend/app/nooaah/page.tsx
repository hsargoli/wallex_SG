"use client";

import { useEffect, useState } from "react";
import {
  Brain,
  Loader2,
  Play,
  FlaskConical,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  ShieldAlert,
  Power,
  Save,
} from "lucide-react";
import {
  useNooaahStatus,
  useNooaahBacktest,
  useNooaahConfig,
  useUpdateNooaahConfig,
  useKillNooaah,
  useResumeNooaah,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EquityChart } from "@/components/charts/equity-chart";

const formatThousands = (s: string): string => {
  // حذف همه‌ی غیر رقم‌ها
  const digits = s.replace(/\D/g, "");
  if (!digits) return "";
  return Number(digits).toLocaleString("en-US");
};

const parseThousands = (s: string): number => {
  const digits = s.replace(/\D/g, "");
  return digits ? Number(digits) : 0;
};


const pnlColor = (v: number) =>
  v > 0 ? "text-emerald-500" : v < 0 ? "text-red-500" : "text-muted-foreground";

const PRESETS = {
  conservative: {
    label: "🟢 احتیاط",
    conf: 85, cc: 2, tp: 3.0, sl: 1.5, vol_z_min: -0.5,
  },
  normal: {
    label: "🟡 عادی",
    conf: 75, cc: 2, tp: 3.0, sl: 1.5, vol_z_min: -0.5,
  },
  aggressive: {
    label: "🔴 تهاجمی",
    conf: 60, cc: 1, tp: 2.0, sl: 1.0, vol_z_min: -1.0,
  },
} as const;

type PresetKey = keyof typeof PRESETS;

export default function NooaahPage() {
  const [top, setTop] = useState(5);
  const [start, setStart] = useState("2026-09-25");
  const [end, setEnd] = useState("2026-10-05");
  const [preset, setPreset] = useState<PresetKey>("conservative");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [conf, setConf] = useState(85);
  const [cc, setCc] = useState(2);
  const [tp, setTp] = useState(3.0);
  const [sl, setSl] = useState(1.5);
  const [volZMin, setVolZMin] = useState(-0.5);
  const [useCustom, setUseCustom] = useState(false);

  const status = useNooaahStatus(top);
  const backtest = useNooaahBacktest();
  const nooaahConfig = useNooaahConfig();
  const updateConfig = useUpdateNooaahConfig();
  const killMut = useKillNooaah();
  const resumeMut = useResumeNooaah();

  const [capitalInput, setCapitalInput] = useState<string>("");
  const [limitInput, setLimitInput] = useState<string>("");

  // وقتی config لود شد، inputها رو پر کن (یک بار)
  const cfg = nooaahConfig.data;
  useEffect(() => {
    if (cfg && capitalInput === "" && limitInput === "") {
      setCapitalInput(formatThousands(String(cfg.capital_total)));
      setLimitInput(String(cfg.daily_loss_limit_pct));
    }
  }, [cfg, capitalInput, limitInput]);

  const applyPreset = (key: PresetKey) => {
    setPreset(key);
    const p = PRESETS[key];
    setConf(p.conf);
    setCc(p.cc);
    setTp(p.tp);
    setSl(p.sl);
    setVolZMin(p.vol_z_min);
  };

  const runBacktest = () => {
    const params = useCustom
      ? { top, start, end, conf, cc, tp, sl, vol_z_min: volZMin }
      : { top, start, end, ...PRESETS[preset] };
    // @ts-expect-error: PRESETS includes label which API ignores
    backtest.mutate(params);
  };

  return (
    <div className="space-y-6 p-6" dir="rtl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Brain className="h-6 w-6 text-amber-400" />
          <h1 className="text-2xl font-bold">ربات نوح — تحلیل و بک‌تست</h1>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">تعداد نمادها:</label>
          <select
            value={top}
            onChange={(e) => setTop(Number(e.target.value))}
            className="rounded-lg border border-border/50 bg-card px-3 py-1.5 text-sm"
          >
            {[3, 5, 8, 10].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Config & Kill Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <Power className="h-4 w-4" />
              پیکربندی و کنترل
            </span>
            {cfg && (
              <span
                className={`rounded-full px-3 py-1 text-xs font-bold ${
                  cfg.killed
                    ? "bg-red-500/15 text-red-500"
                    : cfg.mode === "live"
                    ? "bg-emerald-500/15 text-emerald-500"
                    : "bg-sky-500/15 text-sky-500"
                }`}
              >
                {cfg.killed
                  ? "🛑 متوقف"
                  : cfg.mode === "live"
                  ? "🔴 زنده"
                  : "🟦 Paper"}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {nooaahConfig.isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              در حال بارگذاری...
            </div>
          )}

          {nooaahConfig.isError && (
            <div className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-500/5 p-3 text-sm text-red-500">
              <AlertCircle className="h-4 w-4" />
              خطا در دریافت پیکربندی — آیا backend اجراست؟
              <button
                onClick={() => nooaahConfig.refetch()}
                className="mr-auto rounded border border-red-500/40 px-2 py-1 text-xs hover:bg-red-500/10"
              >
                تلاش مجدد
              </button>
            </div>
          )}

          {cfg && (
            <>
              {/* kill banner */}
              {cfg.killed && (
                <div className="flex items-center justify-between rounded-xl border border-red-500/40 bg-red-500/5 p-3">
                  <div className="flex items-center gap-2 text-sm text-red-500">
                    <ShieldAlert className="h-4 w-4" />
                    ربات متوقف شده — هیچ سفارش جدیدی پذیرفته نمی‌شود.
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => resumeMut.mutate()}
                    disabled={resumeMut.isPending}
                  >
                    ادامه
                  </Button>
                </div>
              )}

              {/* daily loss banner */}
              {!cfg.killed && cfg.daily_loss_hit && (
                <div className="flex items-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/5 p-3 text-sm text-amber-500">
                  <AlertCircle className="h-4 w-4" />
                  سقف ضرر روزانه پر شده ({cfg.daily_pnl_pct.toFixed(2)}٪). ربات تا فردا می‌خوابد.
                </div>
              )}

              {/* capital + limit grid */}
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                  سرمایه‌ی کل (تومان)
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      inputMode="numeric"
                      dir="ltr"
                      value={capitalInput}
                      onChange={(e) =>
                        setCapitalInput(formatThousands(e.target.value))
                      }
                      className="h-9 flex-1 rounded-lg border border-border bg-background px-3 text-sm font-mono text-left"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        updateConfig.mutate({
                          capital_total: parseThousands(capitalInput),
                        })
                      }
                      disabled={updateConfig.isPending}
                    >
                      <Save className="h-3 w-3" />
                    </Button>
                  </div>
                </label>
                <label className="flex flex-col gap-1 text-xs text-muted-foreground">
                  سقف ضرر روزانه (٪)
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={limitInput}
                      onChange={(e) => setLimitInput(e.target.value)}
                      step={0.1}
                      className="h-9 flex-1 rounded-lg border border-border bg-background px-3 text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        updateConfig.mutate({
                          daily_loss_limit_pct: Number(limitInput),
                        })
                      }
                      disabled={updateConfig.isPending}
                    >
                      <Save className="h-3 w-3" />
                    </Button>
                  </div>
                </label>
              </div>

              {/* stats */}
              <div className="grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
                <div className="rounded-lg border border-border/40 p-2">
                  <div className="text-muted-foreground">آزاد</div>
                  <div className="font-mono font-bold">
                    {cfg.capital_available.toLocaleString()}
                  </div>
                </div>
                <div className="rounded-lg border border-border/40 p-2">
                  <div className="text-muted-foreground">در پوزیشن</div>
                  <div className="font-mono font-bold">
                    {cfg.capital_in_use.toLocaleString()}
                  </div>
                </div>
                <div className="rounded-lg border border-border/40 p-2">
                  <div className="text-muted-foreground">پوزیشن باز</div>
                  <div className="font-mono font-bold">{cfg.open_positions_count}</div>
                </div>
                <div className="rounded-lg border border-border/40 p-2">
                  <div className="text-muted-foreground">Scheduler</div>
                  <div className="font-mono font-bold">
                    {cfg.scheduler_running ? "🟢 فعال" : "⚪ خاموش"}
                  </div>
                </div>
              </div>

              {/* kill button */}
              {!cfg.killed && (
                <Button
                  variant="destructive"
                  onClick={() => {
                    if (confirm("مطمئنی؟ این کار همه‌ی پوزیشن‌های باز رو متوقف می‌کنه.")) {
                      killMut.mutate();
                    }
                  }}
                  disabled={killMut.isPending}
                  className="w-full"
                >
                  <ShieldAlert className="h-4 w-4" />
                  <span className="mr-2">توقف اضطراری (Kill-Switch)</span>
                </Button>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Settings Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">تنظیمات اجرا</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Date range + top */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
              از تاریخ
              <input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                className="h-9 rounded-lg border border-border bg-background px-3 text-sm text-foreground"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
              تا تاریخ
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                className="h-9 rounded-lg border border-border bg-background px-3 text-sm text-foreground"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-muted-foreground">
              تعداد نمادها
              <select
                value={top}
                onChange={(e) => setTop(Number(e.target.value))}
                className="h-9 rounded-lg border border-border bg-background px-3 text-sm"
              >
                {[3, 5, 8, 10].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>
          </div>

          {/* Preset selector */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">حالت:</span>
            {(Object.keys(PRESETS) as PresetKey[]).map((k) => (
              <button
                key={k}
                onClick={() => { applyPreset(k); setUseCustom(false); }}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-all ${
                  preset === k && !useCustom
                    ? "border-primary bg-primary/10 font-bold"
                    : "border-border/50 hover:bg-muted/50"
                }`}
              >
                {PRESETS[k].label}
              </button>
            ))}
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="rounded-lg border border-border/50 px-3 py-1.5 text-xs hover:bg-muted/50"
            >
              {showAdvanced ? "بستن" : "تنظیمات پیشرفته"}
            </button>
          </div>

          {/* Advanced override */}
          {showAdvanced && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
              <NumField label="min_confidence" value={conf} onChange={(v) => { setConf(v); setUseCustom(true); }} />
              <NumField label="confirmation" value={cc} onChange={(v) => { setCc(v); setUseCustom(true); }} />
              <NumField label="tp_atr" value={tp} onChange={(v) => { setTp(v); setUseCustom(true); }} step={0.1} />
              <NumField label="sl_atr" value={sl} onChange={(v) => { setSl(v); setUseCustom(true); }} step={0.1} />
              <NumField label="vol_z_min" value={volZMin} onChange={(v) => { setVolZMin(v); setUseCustom(true); }} step={0.1} />
            </div>
          )}

          {/* Run button */}
          <Button
            onClick={runBacktest}
            disabled={backtest.isPending}
            className="w-full md:w-auto"
          >
            {backtest.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FlaskConical className="h-4 w-4" />
            )}
            <span className="mr-2">
              {backtest.isPending ? "در حال اجرا..." : "اجرای بک‌تست"}
            </span>
          </Button>
        </CardContent>
      </Card>

      {/* Status Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            <span>وضعیت زنده</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => status.refetch()}
              disabled={status.isFetching}
            >
              {status.isFetching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              <span className="mr-2">تحلیل الان</span>
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {status.isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              در حال تحلیل...
            </div>
          )}

          {status.data && (
            <div className="space-y-3">
              <div className="text-sm">
                <span className="text-muted-foreground">نمادهای بررسی‌شده: </span>
                <span className="font-mono text-xs">
                  {status.data.symbols_analyzed.join("، ")}
                </span>
                <span className="text-xs text-muted-foreground mr-2">
                  ({status.data.duration_seconds}s)
                </span>
              </div>

              {status.data.proposal ? (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
                  <div className="mb-2 flex items-center gap-2 text-emerald-500">
                    <TrendingUp className="h-4 w-4" />
                    <span className="font-bold">
                      پیشنهاد: {status.data.proposal.symbol}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                    <div>
                      <div className="text-xs text-muted-foreground">ورود</div>
                      <div className="font-mono font-bold">
                        {status.data.proposal.entry.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">حد سود</div>
                      <div className="font-mono font-bold text-emerald-500">
                        {status.data.proposal.take_profit.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">حد ضرر</div>
                      <div className="font-mono font-bold text-red-500">
                        {status.data.proposal.stop_loss.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">اطمینان</div>
                      <div className="font-mono font-bold">
                        {status.data.proposal.confidence}٪
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    {status.data.proposal.reason}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 rounded-xl border border-border/50 bg-muted/30 p-4 text-sm text-muted-foreground">
                  <AlertCircle className="h-4 w-4" />
                  الان هیچ نمادی روند صعودی معتبر با اطمینان کافی نداره — ربات منتظره.
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backtest Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">نتایج بک‌تست</CardTitle>
        </CardHeader>
        <CardContent>
          {backtest.error && (
            <div className="text-sm text-red-500">
              خطا: {(backtest.error as Error).message}
            </div>
          )}

          {backtest.data && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Stat label="معاملات" value={String(backtest.data.total_trades)} />
                <Stat
                  label="برد / باخت"
                  value={`${backtest.data.wins} / ${backtest.data.losses}`}
                />
                <Stat
                  label="نرخ برد"
                  value={`${backtest.data.win_rate.toFixed(1)}٪`}
                />
                <Stat
                  label="بازده کل"
                  value={`${backtest.data.total_return_pct >= 0 ? "+" : ""}${backtest.data.total_return_pct.toFixed(2)}٪`}
                  color={pnlColor(backtest.data.total_return_pct)}
                />
                <Stat
                  label="حداکثر افت"
                  value={`${backtest.data.max_drawdown_pct.toFixed(2)}٪`}
                  color="text-amber-500"
                />
                <Stat
                  label="ضریب سود"
                  value={backtest.data.profit_factor.toFixed(2)}
                />
                <Stat
                  label="شارپ"
                  value={backtest.data.sharpe_ratio.toFixed(3)}
                />
                <Stat
                  label="میانگین مدت"
                  value={`${backtest.data.avg_duration_candles.toFixed(1)}h`}
                />
              </div>

              <div className="rounded-xl border border-border/50 bg-card p-3">
                <div className="mb-2 text-sm font-medium text-muted-foreground">
                  نمودار رشد سرمایه
                </div>
                <EquityChart
                  series={[
                    {
                      name: "ربات نوح",
                      data: backtest.data.equity_curve_full,
                      color: "#10b981",
                    },
                    {
                      name: "خرید و نگه‌داری (میانگین ۵ نماد)",
                      data: backtest.data.buy_hold_curve,
                      color: "#94a3b8",
                      dashed: true,
                    },
                  ]}
                />
              </div>

              {backtest.data.recent_trades.length > 0 && (
                <div>
                  <div className="mb-2 text-sm font-medium text-muted-foreground">
                    آخرین معاملات
                  </div>
                  <div className="space-y-1 text-xs">
                    {backtest.data.recent_trades.map((t: import("@/lib/api").NooaahTrade, i: number) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded border border-border/40 px-3 py-2"
                      >
                        <span className="font-mono">
                          {Number(t.entry_price).toLocaleString()} →{" "}
                          {Number(t.exit_price).toLocaleString()}
                        </span>
                        <span className="text-muted-foreground">{t.exit_reason}</span>
                        <span className={pnlColor(t.return_pct)}>
                          {t.return_pct >= 0 ? "+" : ""}
                          {t.return_pct.toFixed(2)}٪
                        </span>
                        <span className="text-muted-foreground">
                          {t.confidence}٪ / {t.duration_candles}h
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!backtest.data && !backtest.isPending && (
            <div className="text-sm text-muted-foreground">
              برای دیدن نتایج، دکمه‌ی «اجرای بک‌تست» رو بزن. (۲۰-۳۰ ثانیه طول می‌کشه)
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function NumField({
  label,
  value,
  onChange,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted-foreground">
      <span className="font-mono">{label}</span>
      <input
        type="number"
        value={value}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-8 rounded-lg border border-border bg-background px-2 text-sm text-foreground"
      />
    </label>
  );
}


function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`mt-1 text-lg font-bold tabular-nums ${color ?? ""}`}>
        {value}
      </div>
    </div>
  );
}
