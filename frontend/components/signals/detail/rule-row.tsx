"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { type SignalRule } from "@/lib/api";

interface RuleRowProps {
  rule: SignalRule;
}

export function RuleRow({ rule }: RuleRowProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border p-3 text-sm",
        rule.passed
          ? "border-emerald-500/20 bg-emerald-500/[0.03]"
          : "border-white/5 bg-white/[0.02]",
      )}
    >
      {rule.passed ? (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
      ) : (
        <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="font-medium">{rule.name}</p>
          <span
            className={cn(
              "shrink-0 font-mono text-xs",
              rule.score > 0 ? "text-emerald-400" : "text-muted-foreground",
            )}
          >
            {rule.score > 0 ? `+${rule.score}` : rule.score}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground">{rule.reason}</p>
      </div>
    </div>
  );
}
