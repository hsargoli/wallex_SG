"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Play } from "lucide-react";

export function BacktestCard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      // Direct fetch to bypass react-query caching for now
      const token = localStorage.getItem("sarvbots_user_token");
      const res = await fetch("/api/backend/v1/user/live-bot/backtest", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("خطا در اجرای بک‌تست");
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>بک‌تست استراتژی</span>
          <Button onClick={runBacktest} disabled={loading} size="sm" variant="outline">
            {loading ? <Loader2 className="w-4 h-4 animate-spin ml-2" /> : <Play className="w-4 h-4 ml-2" />}
            اجرای بک‌تست (۳۸ روز)
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="text-sm text-red-500">{error}</p>}
        
        {!data && !loading && !error && (
          <p className="text-sm text-muted-foreground">برای مشاهده عملکرد استراتژی روی داده‌های تاریخی، دکمه بالا را بزنید.</p>
        )}

        {data && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted/20 rounded-lg">
              <div>
                <p className="text-xs text-muted-foreground mb-1">سود/ضرر کل</p>
                <p className={`text-xl font-bold ${data.total_pnl > 0 ? "text-green-500" : "text-red-500"}`} dir="ltr">
                  {data.total_pnl_pct > 0 ? "+" : ""}{data.total_pnl_pct.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">تعداد تریدها</p>
                <p className="text-xl font-bold">{data.total_trades}</p>
              </div>
            </div>

            {data.trades && data.trades.length > 0 && (
              <div className="max-h-48 overflow-y-auto border rounded-md">
                <table className="w-full text-sm">
                  <thead className="bg-muted sticky top-0">
                    <tr>
                      <th className="p-2 text-right">نتیجه</th>
                      <th className="p-2 text-left">سود/ضرر (تومان)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.trades.map((t: any, i: number) => (
                      <tr key={i} className="border-t border-border/50">
                        <td className="p-2 text-right">{t.reason}</td>
                        <td className={`p-2 text-left font-mono ${t.pnl > 0 ? "text-green-500" : "text-red-500"}`} dir="ltr">
                          {t.pnl > 0 ? "+" : ""}{t.pnl.toFixed(0)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
