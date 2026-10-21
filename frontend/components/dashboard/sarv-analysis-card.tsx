"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { SarvLogo } from "@/components/landing/sarv-logo";

const SARV_TIPS = [
  "صبر در بازارهای مالی، کلید اصلی سودآوری است. سرو هم در سکوت رشد می‌کند.",
  "نوسانات کوتاه‌مدت، بخشی طبیعی از چرخه بازار هستند. نگران بادهای زودگذر نباش.",
  "همیشه قبل از ورود به معامله، حد ضرر (Stop Loss) خود را مشخص کنید.",
  "در اوج هیجان خرید و ترس از فروش، هرگز تصمیمات احساسی نگیرید.",
  "روند اصلی بازار دوست شماست؛ سعی نکنید در خلاف جهت روند حرکت کنید."
];

export function SarvAnalysisCard() {
  const [dailyTip, setDailyTip] = useState("");

  useEffect(() => {
    setDailyTip(SARV_TIPS[Math.floor(Math.random() * SARV_TIPS.length)]);
  }, []);

  return (
    <Card className="border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-transparent backdrop-blur-sm">
      <CardContent className="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-5">
        <div className="shrink-0 p-2 rounded-2xl bg-violet-500/10">
          <SarvLogo size={40} />
        </div>
        <div className="space-y-1.5 flex-1">
          <h3 className="text-sm font-bold text-foreground">
            بیت‌کوین هم مثل سرو همیشه سبز بوده
          </h3>
          <p className="text-[11px] leading-relaxed text-muted-foreground/80 flex items-center gap-1.5">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0"></span>
            {dailyTip}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
