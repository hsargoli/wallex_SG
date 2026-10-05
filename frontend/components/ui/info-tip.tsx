"use client";

import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface InfoTipProps {
  text: string;
  className?: string;
}

export function InfoTip({ text, className }: InfoTipProps) {
  return (
    <span
      title={text}
      className={cn(
        "inline-flex cursor-help items-center text-muted-foreground/50 transition hover:text-muted-foreground",
        className,
      )}
    >
      <Info className="h-3 w-3" />
    </span>
  );
}
