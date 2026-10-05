"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { type MultiTfSignal } from "@/lib/api";
import { signalConfig } from "./_helpers";
import { cn } from "@/lib/utils";

interface MultiTfCardProps {
  timeframe: string;
  data?: MultiTfSignal;
  loading: boolean;
  active: boolean;
  onClick: () => void;
}

export function MultiTfCard({
  timeframe,
  data,
  loading,
  active,
  onClick,
}: MultiTfCardProps) {
  const config = signalConfig(data?.signal);
  const Icon = config.icon;

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 rounded-xl border bg-card p-4 text-right transition",
        active
          ? "border-emerald-500/40 bg-emerald-500/5"
          : "border-white/5 hover:border-white/10",
      )}
    >
      <Icon className={cn("h-6 w-6", config.color)} />
      <div className="flex-1">
        <p className="font-mono text-xs text-muted-foreground">{timeframe}</p>
        {loading ? (
          <Skeleton className="mt-1 h-5 w-16" />
        ) : (
          <p className={cn("text-sm font-semibold", config.color)}>
            {config.label}
          </p>
        )}
      </div>
      {data?.confidence !== undefined && data.confidence > 0 && (
        <span className="font-mono text-[10px] text-muted-foreground">
          {data.confidence}%
        </span>
      )}
    </button>
  );
}
