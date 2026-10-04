"use client";

import { useState, useEffect } from "react";
import { ChevronRight, ChevronLeft, CornerDownLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  const [jumpValue, setJumpValue] = useState(String(page));

  // Sync input with current page
  useEffect(() => {
    setJumpValue(String(page));
  }, [page]);

  if (totalPages <= 1) return null;

  // Build pages array with "..." for large ranges
  const pages: (number | "...")[] = [];
  const window = 2;

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

  const handleJump = () => {
    const n = Number(jumpValue);
    if (!Number.isFinite(n)) {
      setJumpValue(String(page));
      return;
    }
    const clamped = Math.max(1, Math.min(totalPages, Math.floor(n)));
    if (clamped !== page) {
      onPageChange(clamped);
    } else {
      setJumpValue(String(clamped));
    }
  };

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

      {/* Jump to page */}
      <div className="mr-2 flex items-center gap-1.5 text-xs text-muted-foreground">
        <span>برو به:</span>
        <Input
          type="number"
          min={1}
          max={totalPages}
          value={jumpValue}
          onChange={(e) => setJumpValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleJump();
            }
          }}
          onBlur={handleJump}
          className="h-8 w-16 text-center font-mono text-xs"
          aria-label="شماره صفحه"
        />
        <Button
          variant="outline"
          size="icon"
          onClick={handleJump}
          className="h-8 w-8"
          aria-label="برو"
          title="برو به صفحه"
        >
          <CornerDownLeft className="h-3.5 w-3.5" />
        </Button>
        <span className="text-[10px] opacity-70">از {totalPages}</span>
      </div>
    </div>
  );
}
