"use client";

import { cn } from "@/lib/utils";

export type PaneSize = "S" | "M" | "L";

export const PANE_HEIGHTS: Record<PaneSize, number> = {
  S: 80,
  M: 120,
  L: 200,
};

interface PaneResizeProps {
  value: PaneSize;
  onChange: (size: PaneSize) => void;
  label: string;
}

export function PaneResize({ value, onChange, label }: PaneResizeProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] text-muted-foreground">{label}:</span>
      <div
        dir="ltr"
        className="inline-flex items-center gap-0.5 rounded-md border border-white/10 bg-background/50 p-0.5"
      >
        {(["S", "M", "L"] as const).map((s) => (
          <button
            key={s}
            onClick={() => onChange(s)}
            className={cn(
              "h-5 w-5 rounded font-mono text-[10px] font-bold transition",
              value === s
                ? "bg-emerald-500/20 text-emerald-400"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
            )}
            title={
              s === "S"
                ? "کوچیک (۸۰px)"
                : s === "M"
                  ? "متوسط (۱۲۰px)"
                  : "بزرگ (۲۰۰px)"
            }
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
