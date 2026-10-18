"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LiveBotStatus } from "@/lib/hooks/use-bear-hunter";

const STATUS_MAP: Record<string, { text: string; cls: string }> = {
  active: { text: "🟢 فعال", cls: "bg-green-500/10 text-green-600 border-green-500/30" },
  waiting_liquidity: { text: "🟡 منتظر نقدینگی والکس", cls: "bg-yellow-500/10 text-yellow-700 border-yellow-500/30" },
  idle: { text: "⚪ متوقف (idle)", cls: "bg-gray-500/10 text-gray-600 border-gray-500/30" },
  no_signal: { text: "⚪ سیگنال تنظیم نشده", cls: "bg-gray-500/10 text-gray-600 border-gray-500/30" },
  signal_expired: { text: "🟠 سیگنال منقضی", cls: "bg-orange-500/10 text-orange-600 border-orange-500/30" },
  signal_not_bearish: { text: "🔵 سیگنال bearish نیست", cls: "bg-blue-500/10 text-blue-600 border-blue-500/30" },
  killed_auto: { text: "🔴 متوقف خودکار", cls: "bg-red-500/10 text-red-600 border-red-500/30" },
  killed_manual: { text: "🔴 متوقف دستی", cls: "bg-red-500/10 text-red-600 border-red-500/30" },
};

export function StatusCard({ data }: { data: LiveBotStatus }) {
  const s = STATUS_MAP[data.bot_status] ?? { text: data.bot_status, cls: "border-muted" };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>وضعیت ربات</span>
          <span className={"px-3 py-1 rounded-full text-xs border " + s.cls}>{s.text}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">سرمایه:</span>
          <span className="font-mono">{data.capital_tmn.toLocaleString("fa-IR")} ت</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">پوزیشن باز:</span>
          <span>{data.positions_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">ترید امروز:</span>
          <span>{data.trades_today}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">حجم امروز:</span>
          <span className="font-mono">{data.daily_volume_tmn.toLocaleString("fa-IR")} ت</span>
        </div>
        {data.signal_direction && (
          <div className="flex justify-between border-t pt-2 mt-2">
            <span className="text-muted-foreground">سیگنال:</span>
            <span className="font-mono">{data.signal_direction}</span>
          </div>
        )}
        {data.signal_expires_at && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">انقضا:</span>
            <span className="text-xs">{new Date(data.signal_expires_at).toLocaleString("fa-IR")}</span>
          </div>
        )}
        {data.signal_note && (
          <div className="pt-2 border-t text-xs">
            <span className="text-muted-foreground">یادداشت: </span>{data.signal_note}
          </div>
        )}
        {data.kill_reason && (
          <div className="pt-2 border-t text-xs text-red-600">
            دلیل توقف: {data.kill_reason}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
