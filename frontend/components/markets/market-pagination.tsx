"use client";

import { ChevronRight, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface MarketPaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function MarketPagination({
  page,
  totalPages,
  onPageChange,
}: MarketPaginationProps) {
  if (totalPages <= 1) return null;

  // Build pages array with "..." for large ranges
  const pages: (number | "...")[] = [];
  const window = 2; // how many around current

  for (let i = 1; i <= totalPages; i++) {
    if (
      i === 1 ||
      i === totalPages ||
      (i >= page - window && i <= page + window)
    ) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== "...") {
      pages.push("...");
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-center gap-1.5 pt-4">
      {/* Prev */}
      <Button
        variant="outline"
        size="icon"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="h-8 w-8"
        aria-label="صفحه قبل"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>

      {/* Page numbers */}
      {pages.map((p, i) =>
        p === "..." ? (
          <span
            key={`ellipsis-${i}`}
            className="px-2 text-xs text-muted-foreground"
          >
            ...
          </span>
        ) : (
          <Button
            key={p}
            variant={p === page ? "default" : "outline"}
            size="sm"
            onClick={() => onPageChange(p)}
            className={cn(
              "h-8 min-w-[32px] font-mono text-xs",
              p === page && "bg-emerald-600 hover:bg-emerald-700",
            )}
          >
            {p}
          </Button>
        ),
      )}

      {/* Next */}
      <Button
        variant="outline"
        size="icon"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="h-8 w-8"
        aria-label="صفحه بعد"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
    </div>
  );
}
