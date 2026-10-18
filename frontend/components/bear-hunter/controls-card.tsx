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
    if (reason.trim().length < 3) return toast.error("دلیل حداقل ۳ کاراکتر");
    kill.mutate(reason.trim(), {
      onSuccess: () => { toast.success("ربات متوقف شد"); setReason(""); },
      onError: (e: any) => toast.error(e?.response?.data?.detail ?? "خطا"),
    });
  };

  const onResume = () => {
    const r = reason.trim() || "user_resume";
    resume.mutate(r, {
      onSuccess: () => { toast.success("ربات فعال شد"); setReason(""); },
      onError: (e: any) => toast.error(e?.response?.data?.detail ?? "خطا"),
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
          placeholder="دلیل (اجباری برای توقف)"
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
