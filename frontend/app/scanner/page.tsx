"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  BarChart3,
  Zap,
  ChevronRight,
  ChevronLeft,
  Loader2,
} from "lucide-react";
import { useScannerList, useScanSymbols } from "@/lib/queries";
import { type TrendResult } from "@/lib/api";
import { formatPrice, formatNumber } from "@/lib/format";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 15;

export default function ScannerPage() {
  const [page, setPage] = useState(1);
  const [quote, setQuote] = useState("TMN");

  const list = useScannerList(page, PAGE_SIZE, quote);
  const [symbolsToScan, setSymbolsToScan] = useState<string[]>([]);

  useEffect(() => {
    if (list.data?.symbols && list.data.symbols.length > 0) {
      setSymbolsToScan(list.data.symbols);
    }
  }, [list.data]);

  const scan = useScanSymbols(symbolsToScan);

  const items = scan.data?.items ?? [];
  const stats = {
    bullish: items.filter((i) => i.direction === "bullish").length,
    bearish: items.filter((i) => i.direction === "bearish").length,
    neutral: items.filter((i) => i.direction === "neutral").length,
  };

  const goPage = (p: number) => {
    setPage(p);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Zap className="h-6 w-6 text-emerald-400" />
            اسکنر بازار
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {list.data
              ? `${formatNumber(list.data.total)} مارکت — صفحه ${list.data.page} از ${list.data.total_pages}`
              : "در حال بارگذاری..."}
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-card p-1">
          {["TMN", "USDT"].map((q) => (
            <button
              key={q}
              onClick={() => {
                setQuote(q);
                setPage(1);
              }}
              className={cn(
                "rounded px-3 py-1.5 text-xs font-medium transition",
                quote === q
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <StatBox label="صعودی" value={stats.bullish} icon={TrendingUp} color="text-emerald-400" loading={scan.isLoading} />
        <StatBox label="نزولی" value={stats.bearish} icon={TrendingDown} color="text-red-400" loading={scan.isLoading} />
        <StatBox label="بدون روند" value={stats.neutral} icon={Minus} color="text-zinc-400" loading={scan.isLoading} />
        <StatBox
          label="صفحه"
          value={`${list.data?.page ?? 1} / ${list.data?.total_pages ?? 1}`}
          icon={BarChart3}
          color="text-blue-400"
          loading={list.isLoading}
        />
      </div>

      <Card>
        <CardHeader className="border-b border-white/5 pb-3">
          <div className="grid grid-cols-[1.5fr_1fr_0.8fr_0.8fr_0.8fr_0.6fr_0.8fr_1.2fr_0.7fr_0.6fr_0.7fr] gap-2 text-[10px] font-medium text-muted-foreground">
            <div>نماد</div>
            <div className="text-left">قیمت</div>
            <div className="text-center">3h</div>
            <div className="text-center">12h</div>
            <div className="text-center">24h</div>
            <div className="text-center">R/R</div>
            <div className="text-center">سیگنال</div>
            <div className="text-center">Score</div>
            <div className="text-center">الگو</div>
            <div className="text-center">نوسان</div>
            <div className="text-center">روند</div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {scan.isLoading || list.isLoading ? (
            <div className="space-y-2 p-4">
              {[...Array(10)].map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {items.map((item) => (
                <ScanRow key={item.symbol} item={item} />
              ))}
              {items.length === 0 && (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  نتیجه‌ای یافت نشد
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {list.data && list.data.total_pages > 1 && (
        <Pagination
          page={page}
          totalPages={list.data.total_pages}
          onPageChange={goPage}
          loading={list.isLoading || scan.isLoading}
        />
      )}
    </div>
  );
}

function Sparkline({
  data,
  direction,
}: {
  data: number[];
  direction: "bullish" | "bearish" | "neutral";
}) {
  if (!data || data.length < 2) return <div className="h-6 w-12" />;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 48;
  const h = 20;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");

  const color =
    direction === "bullish"
      ? "#10b981"
      : direction === "bearish"
        ? "#ef4444"
        : "#a1a1aa";

  return (
    <svg width={w} height={h} className="flex-shrink-0 opacity-90">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

function Pagination({
  page,
  totalPages,
  onPageChange,
  loading,
}: {
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
  loading: boolean;
}) {
  const pages = buildPageList(page, totalPages);

  return (
    <div className="flex flex-wrap items-center justify-center gap-1">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1 || loading}
        className="gap-1"
      >
        <ChevronRight className="h-3.5 w-3.5" />
        قبلی
      </Button>

      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`e-${i}`} className="px-2 text-muted-foreground">
            ...
          </span>
        ) : (
          <Button
            key={p}
            variant={p === page ? "default" : "outline"}
            size="sm"
            onClick={() => onPageChange(p as number)}
            disabled={loading}
            className={cn(
              "h-8 w-8 p-0 font-mono text-xs",
              p === page && "bg-emerald-600 hover:bg-emerald-700",
            )}
          >
            {p}
          </Button>
        ),
      )}

      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages || loading}
        className="gap-1"
      >
        بعدی
        <ChevronLeft className="h-3.5 w-3.5" />
      </Button>

      {loading && (
        <div className="ml-2 flex items-center gap-1 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          در حال اسکن...
        </div>
      )}
    </div>
  );
}

function buildPageList(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "...")[] = [1];
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  if (start > 2) pages.push("...");
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < total - 1) pages.push("...");
  pages.push(total);
  return pages;
}

function ScanRow({ item }: { item: TrendResult }) {
  const config = directionConfig(item.direction);
  const Icon = config.icon;

  return (
    <Link
      href={`/signals/${item.symbol}`}
      className="grid grid-cols-[1.5fr_1fr_0.8fr_0.8fr_0.8fr_0.6fr_0.8fr_1.2fr_0.7fr_0.6fr_0.7fr] items-center gap-2 px-4 py-3 transition hover:bg-white/[0.02]"
    >
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4 flex-shrink-0", config.color)} />
        <div className="min-w-0">
          <p className="truncate font-mono text-sm font-semibold">{item.symbol}</p>
          <p className="truncate font-mono text-[10px] text-muted-foreground">
            {formatPrice(item.current_price)}
          </p>
        </div>
        <Sparkline data={item.sparkline} direction={item.direction} />
      </div>

      <ChangeCell value={item.change_3h} />
      <ChangeCell value={item.change_12h} />
      <ChangeCell value={item.change_24h} />

      <div className="text-center">
        {item.risk_reward ? (
          <span
            className={cn(
              "font-mono text-xs font-bold",
              Number(item.risk_reward) >= 2
                ? "text-emerald-400"
                : Number(item.risk_reward) >= 1
                  ? "text-amber-400"
                  : "text-red-400",
            )}
          >
            {Number(item.risk_reward).toFixed(1)}
          </span>
        ) : (
          <span className="text-[10px] text-muted-foreground/50">—</span>
        )}
      </div>

      <div className="text-center">
        <SignalBadge signal={item.signal} />
      </div>

      <div className="flex items-center justify-center gap-1">
        <div className="h-1.5 w-12 overflow-hidden rounded-full bg-white/5">
          <div
            className={cn(
              "h-full transition-all",
              item.trend_score > 0 ? "bg-emerald-500" : "bg-red-500",
            )}
            style={{ width: `${Math.min(Math.abs(item.trend_score), 100)}%` }}
          />
        </div>
        <span className={cn("font-mono text-xs font-bold", config.color)}>
          {item.trend_score > 0 ? "+" : ""}
          {item.trend_score}
        </span>
      </div>

      <div className="text-center">
        <Badge variant="outline" className={cn("text-[9px]", patternColor(item.pattern))}>
          {patternLabel(item.pattern)}
        </Badge>
      </div>

      <div className="text-center font-mono text-[10px] text-muted-foreground">
        {Number(item.volatility_pct).toFixed(1)}%
      </div>

      <div className="text-center">
        <Badge variant="outline" className={cn("text-[9px]", strengthColor(item.strength))}>
          {strengthLabel(item.strength)}
        </Badge>
      </div>
    </Link>
  );
}

function ChangeCell({ value }: { value: string | null }) {
  if (value === null) {
    return <div className="text-center text-[10px] text-muted-foreground/50">—</div>;
  }
  const n = Number(value);
  const isUp = n >= 0;
  return (
    <div className="text-center">
      <span
        className={cn(
          "font-mono text-[11px] font-medium",
          isUp ? "text-emerald-400" : "text-red-400",
        )}
      >
        {isUp ? "+" : ""}
        {n.toFixed(2)}%
      </span>
    </div>
  );
}

function SignalBadge({ signal }: { signal: "buy" | "sell" | "hold" }) {
  const config = {
    buy: { label: "خرید", cls: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400" },
    sell: { label: "فروش", cls: "border-red-500/40 bg-red-500/10 text-red-400" },
    hold: { label: "صبر", cls: "border-amber-500/40 bg-amber-500/10 text-amber-400" },
  }[signal];
  return (
    <Badge variant="outline" className={cn("text-[10px] font-semibold", config.cls)}>
      {config.label}
    </Badge>
  );
}

function StatBox({
  label,
  value,
  icon: Icon,
  color,
  loading,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  loading: boolean;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <Icon className={cn("h-8 w-8", color)} />
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="mt-1 h-6 w-12" />
          ) : (
            <p className={cn("font-mono text-xl font-bold", color)}>{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function directionConfig(d: string) {
  return (
    {
      bullish: { icon: TrendingUp, color: "text-emerald-400" },
      bearish: { icon: TrendingDown, color: "text-red-400" },
      neutral: { icon: Minus, color: "text-zinc-400" },
    }[d] ?? { icon: Activity, color: "text-zinc-400" }
  );
}

function strengthLabel(s: string): string {
  return { weak: "ضعیف", medium: "متوسط", strong: "قوی" }[s] ?? s;
}

function strengthColor(s: string): string {
  return (
    {
      weak: "border-white/10 text-zinc-400",
      medium: "border-amber-500/30 text-amber-400",
      strong: "border-emerald-500/30 text-emerald-400",
    }[s] ?? ""
  );
}

function patternLabel(p: string): string {
  return { trending: "روند", choppy: "نوسانی", ranging: "محدوده" }[p] ?? p;
}

function patternColor(p: string): string {
  return (
    {
      trending: "border-blue-500/30 text-blue-400",
      choppy: "border-amber-500/30 text-amber-400",
      ranging: "border-zinc-500/30 text-zinc-400",
    }[p] ?? ""
  );
}
