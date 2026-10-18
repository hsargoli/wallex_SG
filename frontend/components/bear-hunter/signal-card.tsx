"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSetLiveBotSignal } from "@/lib/hooks/use-bear-hunter";
import { toast } from "sonner";

export function SignalCard() {
  const [note, setNote] = useState("");
  const mut = useSetLiveBotSignal();

  const setSig = (direction: "bearish" | "bullish" | "neutral") => {
    mut.mutate(
      { direction, ttl_days: 10, note: note.trim() || undefined },
      {
        onSuccess: () => { toast.success("سیگنال " + direction + " تنظیم شد"); setNote(""); },
        onError: (e: any) => toast.error(e?.response?.data?.detail ?? "خطا"),
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>تنظیم سیگنال</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <input
          type="text"
          placeholder="یادداشت (اختیاری)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          className="w-full px-3 py-2 rounded-md border bg-background text-sm"
        />
        <div className="grid grid-cols-3 gap-2">
          <Button onClick={() => setSig("bearish")} disabled={mut.isPending} className="bg-red-600 hover:bg-red-700 text-white">
            نزولی
          </Button>
          <Button onClick={() => setSig("neutral")} disabled={mut.isPending} variant="outline">
            خنثی
          </Button>
          <Button onClick={() => setSig("bullish")} disabled={mut.isPending} variant="outline">
            صعودی
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          TTL پیش‌فرض ۱۰ روز. ربات فقط در حالت bearish معامله می‌کند.
        </p>
      </CardContent>
    </Card>
  );
}
