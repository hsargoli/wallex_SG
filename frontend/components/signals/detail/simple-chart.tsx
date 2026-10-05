"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { type Candle } from "@/lib/api";

interface SimpleChartProps {
  candles: Candle[];
  height?: number;
  loading?: boolean;
}

/**
 * چارت ساده — فقط کندل + حجم.
 * بدون EMA، Bollinger، سطوح، پنل لایه‌ها.
 * مناسب صفحه‌ی سیگنال برای کاربر تازه‌کار.
 */
export function SimpleChart({
  candles,
  height = 320,
  loading = false,
}: SimpleChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "Vazirmatn, system-ui, sans-serif",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.03)" },
        horzLines: { color: "rgba(255, 255, 255, 0.03)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.06)",
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.06)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 0,
        vertLine: {
          color: "rgba(16, 185, 129, 0.5)",
          width: 1,
          style: 2,
        },
        horzLine: {
          color: "rgba(16, 185, 129, 0.5)",
          width: 1,
          style: 2,
        },
      },
      width: containerRef.current.clientWidth,
      height,
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderUpColor: "#10b981",
      borderDownColor: "#ef4444",
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#3f3f46",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry || !chartRef.current) return;
      const w = entry.contentRect.width;
      if (w > 0) chartRef.current.applyOptions({ width: w });
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;
    if (!candles || candles.length === 0) {
      candleSeriesRef.current.setData([]);
      volumeSeriesRef.current.setData([]);
      return;
    }

    const sorted = [...candles].sort((a, b) => a.time - b.time);

    candleSeriesRef.current.setData(
      sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        open: Number(c.open),
        high: Number(c.high),
        low: Number(c.low),
        close: Number(c.close),
      })),
    );

    volumeSeriesRef.current.setData(
      sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        value: Number(c.volume),
        color:
          Number(c.close) >= Number(c.open)
            ? "rgba(16, 185, 129, 0.3)"
            : "rgba(239, 68, 68, 0.3)",
      })),
    );

    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return (
    <div className="relative w-full" dir="ltr">
      <div ref={containerRef} className="w-full" />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="text-sm text-muted-foreground">
            در حال بارگذاری چارت...
          </div>
        </div>
      )}
      {!loading && (!candles || candles.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-sm text-muted-foreground">
            داده‌ای برای نمایش نیست
          </div>
        </div>
      )}
    </div>
  );
}
