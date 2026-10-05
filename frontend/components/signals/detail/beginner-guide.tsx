"use client";

import { Target, Lightbulb, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface BeginnerGuideProps {
  /** دلایل ساده از signal.reasons */
  reasons: string[];
  /** آیا سیگنال خرید یا فروش داریم */
  signalType: "buy" | "sell" | "hold";
}

export function BeginnerGuide({ reasons, signalType }: BeginnerGuideProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {/* ۱. حد سود و ضرر */}
      <Card className="border-white/5 bg-card">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-bold">
            <Target className="h-4 w-4 text-emerald-400" />
            حد سود و ضرر چیه؟
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
          <p>
            <span className="font-bold text-emerald-400">حد سود (TP):</span>{" "}
            قیمتی که اگه برسه، پوزیشن خودکار بسته می‌شه و سود می‌گیری.
          </p>
          <p>
            <span className="font-bold text-red-400">حد ضرر (SL):</span> قیمتی
            که اگه برسه، پوزیشن بسته می‌شه تا از ضرر بیشتر جلوگیری کنه.
          </p>
          <p className="pt-1 text-[11px] text-muted-foreground/70">
            همیشه از هر دو استفاده کن — نذار ضرر بزرگ شه.
          </p>
        </CardContent>
      </Card>

      {/* ۲. چرا این سیگنال؟ */}
      <Card className="border-white/5 bg-card">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-bold">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            چرا این سیگنال؟
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
          {reasons.length === 0 ? (
            <p className="text-muted-foreground/70">
              دلایلی برای این سیگنال ثبت نشده.
            </p>
          ) : (
            <ul className="space-y-1.5">
              {reasons.map((r, i) => (
                <li key={i} className="flex gap-2">
                  <span className="shrink-0 text-amber-400">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* ۳. قبل از خرید */}
      <Card className="border-amber-500/20 bg-amber-500/[0.03]">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-bold">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            قبل از {signalType === "sell" ? "فروش" : "خرید"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
          <ul className="space-y-1.5">
            <li className="flex gap-2">
              <span className="shrink-0 text-amber-400">•</span>
              <span>فقط با پولی معامله کن که تحمل از دست دادنش رو داری.</span>
            </li>
            <li className="flex gap-2">
              <span className="shrink-0 text-amber-400">•</span>
              <span>
                اگه تازه‌کاری، اول با Paper Trading تست کن.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="shrink-0 text-amber-400">•</span>
              <span>حتماً از حد ضرر (SL) استفاده کن.</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
