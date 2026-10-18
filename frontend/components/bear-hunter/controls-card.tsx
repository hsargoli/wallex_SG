"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useKillLiveBot, useResumeLiveBot } from "@/lib/hooks/use-bear-hunter";
import { toast } from "sonner";

export function ControlsCard({ isKilled, idle }: { isKilled: boolean; idle: boolean }) {
  const [reason, setReason] = useState("");
  const kill = useKillLiveBot();
  const resume = useResumeLiveBot();

  const onKill = () => {
    // Kill switch must be instant! If no reason, use a default.
    const finalReason = reason.trim() || "manual_kill_from_ui";
    kill.mutate(finalReason, {
      onSuccess: () => { toast.success("ربات با موفقیت متوقف شد"); setReason(""); },
      onError: (e: any) => toast.error(e?.response?.data?.detail ?? "خطا در توقف"),
    });
  };

  const onResume = () => {
    // Resume also uses default reason if empty
    const finalReason = reason.trim() || "manual_resume_from_ui";
    resume.mutate(finalReason, {
      onSuccess: () => { toast.success("ربات فعال شد"); setReason(""); },
      onError: (e: any) => toast.error(e?.response?.data?.detail ?? "خطا در فعال‌سازی"),
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>کنترل</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <input
          type="text"
          placeholder="دلیل (اختیاری - برای لاگ)"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full px-3 py-2 rounded-md border bg-background text-sm"
        />
        <div className="grid grid-cols-2 gap-2">
          <Button onClick={onKill} disabled={kill.isPending || (isKilled && idle)} variant="destructive">
            🛑 توقف فوری
          </Button>
          <Button onClick={onResume} disabled={resume.isPending || (!isKilled && !idle)} variant="default">
            ▶️ فعال‌سازی
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          توقف فوری، kill switch را فعال می‌کند. فعال‌سازی، هم kill و هم idle را پاک می‌کند.
        </p>
      </CardContent>
    </Card>
  );
}
