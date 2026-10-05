"use client";

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  LineSeries,
  LineStyle,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { Eye, EyeOff, Layers } from "lucide-react";
import {
  type IndicatorsResponse,
  type LevelsResponse,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SignalsChartProps {
  indicators: IndicatorsResponse;
  levels?: LevelsResponse;
  height?: number;
}

interface Layer {
  key: string;
  label: string;
  color: string;
  enabled: boolean;
}

const DEFAULT_LAYERS: Layer[] = [
  { key: "ema9", label: "EMA(9)", color: "text-emerald-400", enabled: true },
  { key: "ema21", label: "EMA(21)", color: "text-orange-400", enabled: true },
  { key: "bollinger", label: "Bollinger", color: "text-purple-400", enabled: true },
  { key: "levels", label: "سطوح (Pivot + S/R)", color: "text-amber-400", enabled: true },
];

export function SignalsChart({ indicators, levels, height = 520 }: SignalsChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const ema9Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const ema21Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbMiddleRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<"Line"> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);

  const [layers, setLayers] = useState<Layer[]>(DEFAULT_LAYERS);


  const toggle = (key: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.key === key ? { ...l, enabled: !l.enabled } : l)),
    );
  };

  // ---------- ایجاد چارت (یک بار) ----------
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "Vazirmatn, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
      timeScale: {
        borderColor: "rgba(255,255,255,0.08)",
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height,
    });

    // کندل
    candleRef.current = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderUpColor: "#10b981",
      borderDownColor: "#ef4444",
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    // EMA خطوط
    ema9Ref.current = chart.addSeries(LineSeries, {
      color: "#10b981",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      visible: true,
    });
    ema21Ref.current = chart.addSeries(LineSeries, {
      color: "#f97316",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    // Bollinger
    bbUpperRef.current = chart.addSeries(LineSeries, {
      color: "rgba(168,85,247,0.6)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    bbMiddleRef.current = chart.addSeries(LineSeries, {
      color: "rgba(168,85,247,0.3)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    bbLowerRef.current = chart.addSeries(LineSeries, {
      color: "rgba(168,85,247,0.6)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      ema9Ref.current = null;
      ema21Ref.current = null;
      bbUpperRef.current = null;
      bbMiddleRef.current = null;
      bbLowerRef.current = null;
      priceLinesRef.current = [];
    };
  }, []);

  // ---------- آپدیت دیتا ----------
  useEffect(() => {
    if (!candleRef.current || !indicators) return;
    const { candles, ema_9, ema_21, bb_upper, bb_middle, bb_lower } = indicators;
    if (!candles.length) return;

    const sortedIdx = candles
      .map((_, i) => i)
      .sort((a, b) => candles[a].time - candles[b].time);

    const pick = <T,>(arr: (T | null)[]): { time: UTCTimestamp; value: number }[] =>
      sortedIdx
        .filter((i) => arr[i] !== null && arr[i] !== undefined)
        .map((i) => ({
          time: candles[i].time as UTCTimestamp,
          value: Number(arr[i]),
        }));

    candleRef.current.setData(
      sortedIdx.map((i) => ({
        time: candles[i].time as UTCTimestamp,
        open: Number(candles[i].open),
        high: Number(candles[i].high),
        low: Number(candles[i].low),
        close: Number(candles[i].close),
      })),
    );

    const ema9Data = pick(ema_9);
    console.log("EMA9 data points:", ema9Data.length, "first:", ema9Data[0], "last:", ema9Data[ema9Data.length - 1]);
    ema9Ref.current?.setData(ema9Data);
    ema21Ref.current?.setData(pick(ema_21));
    bbUpperRef.current?.setData(pick(bb_upper));
    bbMiddleRef.current?.setData(pick(bb_middle));
    bbLowerRef.current?.setData(pick(bb_lower));

    chartRef.current?.timeScale().fitContent();
  }, [indicators]);

  // ---------- خطوط سطوح (Pivot + S/R) ----------
  useEffect(() => {
    if (!candleRef.current) return;

    // پاک کردن خطوط قبلی
    priceLinesRef.current.forEach((line) => {
      try {
        candleRef.current?.removePriceLine(line);
      } catch {
        /* noop */
      }
    });
    priceLinesRef.current = [];

    const levelsEnabled = layers.find((l) => l.key === "levels")?.enabled;
    if (!levelsEnabled || !levels) return;

    const addLine = (
      price: number,
      color: string,
      title: string,
      style: LineStyle = LineStyle.Solid,
    ) => {
      if (!candleRef.current || !Number.isFinite(price)) return;
      const line = candleRef.current.createPriceLine({
        price,
        color,
        lineWidth: 1,
        lineStyle: style,
        axisLabelVisible: true,
        title,
      });
      priceLinesRef.current.push(line);
    };

    // Pivot
    if (levels.pivot) {
      addLine(Number(levels.pivot.pp), "rgba(251,191,36,0.8)", "PP");
      addLine(Number(levels.pivot.r1), "rgba(239,68,68,0.5)", "R1", LineStyle.Dashed);
      addLine(Number(levels.pivot.s1), "rgba(16,185,129,0.5)", "S1", LineStyle.Dashed);
    }

    // S/R (قوی‌ها)
    levels.swings.slice(0, 6).forEach((sw) => {
      const color =
        sw.type === "support"
          ? "rgba(16,185,129,0.6)"
          : "rgba(239,68,68,0.6)";
      const prefix = sw.type === "support" ? "S" : "R";
      addLine(
        Number(sw.price),
        color,
        `${prefix} (${sw.touches}×)`,
        LineStyle.Dotted,
      );
    });
  }, [levels, layers]);

  return (
    <Card>
      <CardHeader className="border-b border-white/5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers className="h-5 w-5 text-emerald-400" />
            چارت تکنیکال با اندیکاتورها
          </CardTitle>

          {/* Layer toggles */}
          <div className="flex flex-wrap items-center gap-2">
            {layers.map((layer) => (
              <Button
                key={layer.key}
                variant="outline"
                size="sm"
                onClick={() => toggle(layer.key)}
                className={cn(
                  "h-7 gap-1.5 text-[11px]",
                  layer.enabled
                    ? "border-white/20 bg-white/5"
                    : "border-white/5 opacity-50",
                )}
              >
                {layer.enabled ? (
                  <Eye className="h-3 w-3" />
                ) : (
                  <EyeOff className="h-3 w-3" />
                )}
                <span className={layer.enabled ? layer.color : ""}>
                  {layer.label}
                </span>
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        <div ref={containerRef} className="w-full" dir="ltr" />
      </CardContent>
    </Card>
  );
}
