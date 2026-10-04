"use client";

import { List, LayoutGrid } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type ViewMode = "list" | "grid";

interface ViewToggleProps {
  value: ViewMode;
  onChange: (v: ViewMode) => void;
}

export function ViewToggle({ value, onChange }: ViewToggleProps) {
  return (
    <div className="flex items-center gap-0.5 rounded-lg border border-border p-0.5">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onChange("list")}
        className={cn(
          "h-7 w-7 rounded-md",
          value === "list" && "bg-emerald-500/15 text-emerald-400",
        )}
        aria-label="نمای لیست"
        title="نمای لیست"
      >
        <List className="h-3.5 w-3.5" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onChange("grid")}
        className={cn(
          "h-7 w-7 rounded-md",
          value === "grid" && "bg-emerald-500/15 text-emerald-400",
        )}
        aria-label="نمای گرید"
        title="نمای گرید"
      >
        <LayoutGrid className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
