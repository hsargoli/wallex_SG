"use client";

import { useState } from "react";
import {
  Brain,
  Loader2,
  Play,
  FlaskConical,
  TrendingUp,
  TrendingDown,
  AlertCircle,
} from "lucide-react";
import { useNooaahStatus, useNooaahBacktest } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EquityChart } from "@/components/charts/equity-chart";

const pnlColor = (v: number) =>
  v > 0 ? "text-emerald-500" : v < 0 ? "text-red-500" : "text-muted-foreground";

export default function NooaahPage() {
  const [top, setTop] = useState(5);
  const status = useNooaahStatus(top);
  const backtest = useNooaahBacktest();

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
          <CardTitle className="flex items-center justify-between text-base">
            <span>بک‌تست</span>
            <Button
              size="sm"
              onClick={() => backtest.mutate({ top, limit: 500 })}
              disabled={backtest.isPending}
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
          </CardTitle>
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
