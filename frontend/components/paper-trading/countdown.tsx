"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  lastCheck: number; // unix seconds
  intervalSec: number;
  isRunning: boolean;
}

const fa = (n: number) => n.toLocaleString("fa-IR");

const TONES = {
  normal: {
    wrap: "border-emerald-500/25 bg-emerald-500/[0.06]",
    text: "text-emerald-600 dark:text-emerald-400",
    fill: "from-emerald-600 via-emerald-500 to-emerald-300",
    glow: "shadow-[0_0_14px_rgba(16,185,129,0.55)]",
    dot: "bg-emerald-400",
    ring: "ring-emerald-400/40",
    label: "چک بعدی ربات",
  },
  urgent: {
    wrap: "border-amber-500/30 bg-amber-500/[0.07]",
    text: "text-amber-600 dark:text-amber-400",
    fill: "from-amber-600 via-amber-500 to-amber-300",
    glow: "shadow-[0_0_14px_rgba(245,158,11,0.6)]",
    dot: "bg-amber-400",
    ring: "ring-amber-400/40",
    label: "ربات در آستانه‌ی چک است",
  },
  checking: {
    wrap: "border-sky-500/30 bg-sky-500/[0.07]",
    text: "text-sky-600 dark:text-sky-400",
    fill: "from-sky-600 via-sky-500 to-sky-300",
    glow: "shadow-[0_0_14px_rgba(14,165,233,0.6)]",
    dot: "bg-sky-400",
    ring: "ring-sky-400/40",
    label: "در حال اسکن بازار…",
  },
} as const;

export function CheckCountdown({ lastCheck, intervalSec, isRunning }: Props) {
  const fallbackBase = useRef(Date.now());
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!isRunning) return;
    fallbackBase.current = Date.now();
    const id = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(id);
  }, [isRunning]);

  if (!isRunning) return null;

  const base = lastCheck ? lastCheck * 1000 : fallbackBase.current;
  const elapsed = Math.max(0, (now - base) / 1000);
  const remaining = Math.max(0, intervalSec - elapsed);
  const progress = Math.min(100, (elapsed / intervalSec) * 100);
  const secondsLeft = Math.ceil(remaining);

  const mode = remaining <= 0 ? "checking" : secondsLeft <= 5 ? "urgent" : "normal";
  const t = TONES[mode];
  const justReset = progress < 1.5;

  return (
    <div
      dir="rtl"
      className={`w-full space-y-3 rounded-xl border px-4 py-3 backdrop-blur-sm transition-colors duration-500 ${t.wrap}`}
    >
      <style>{`
        @keyframes cd-shimmer {
          0%   { transform: translateX(120%); }
          100% { transform: translateX(-120%); }
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${t.dot}`} />
            <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${t.dot}`} />
          </span>
          <span className="text-xs font-medium text-foreground/80">{t.label}</span>
        </div>

        <div className={`flex items-baseline gap-1 tabular-nums ${t.text}`}>
          {mode === "checking" ? (
            <span className="text-sm font-bold">لحظه‌ای…</span>
          ) : (
            <>
              <span className="text-2xl font-extrabold leading-none">{fa(secondsLeft)}</span>
              <span className="text-[11px] font-medium opacity-80">ثانیه</span>
            </>
          )}
        </div>
      </div>

      {/* Track */}
      <div className="relative px-2">
        <div className="relative h-2 w-full rounded-full bg-zinc-300/60 ring-1 ring-black/5 dark:bg-zinc-800/70 dark:ring-white/5">
          {/* Fill */}
          <div
            className={`absolute right-0 top-0 h-full overflow-hidden rounded-full bg-gradient-to-l ease-linear ${t.fill} ${t.glow} ${
              justReset ? "" : "transition-[width] duration-100"
            }`}
            style={{ width: `${progress}%` }}
          >
            <div
              className="absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent via-white/50 to-transparent"
              style={{ animation: "cd-shimmer 1.8s linear infinite" }}
            />
          </div>

          {/* Tick marks */}
          <div
            className="pointer-events-none absolute inset-0 rounded-full"
            style={{
              backgroundImage:
                "repeating-linear-gradient(to left, transparent 0, transparent calc(10% - 1px), rgba(128,128,128,0.35) calc(10% - 1px), rgba(128,128,128,0.35) 10%)",
            }}
          />

          {/* Moving dot */}
          <div
            className={`absolute top-1/2 ease-linear ${justReset ? "" : "transition-[right] duration-100"}`}
            style={{ right: `${progress}%`, transform: "translate(50%, -50%)" }}
          >
            <span className={`absolute inset-0 animate-ping rounded-full opacity-40 ${t.dot}`} />
            <span
              className={`relative block h-4 w-4 rounded-full border-2 border-white shadow-lg ring-4 dark:border-zinc-900 ${t.dot} ${t.ring}`}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>چک قبلی</span>
        <span className="tabular-nums">{fa(Math.round(progress))}٪</span>
        <span>چک بعدی</span>
      </div>
    </div>
  );
}
