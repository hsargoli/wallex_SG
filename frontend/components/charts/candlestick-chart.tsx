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

interface CandlestickChartProps {
  candles: Candle[];
  height?: number;
  loading?: boolean;
  interactive?: boolean;
  showVolume?: boolean;
}

export function CandlestickChart({
  candles,
  height = 400,
  loading = false,
  interactive = true,
  showVolume = false,
}: CandlestickChartProps) {
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
        fontSize: interactive ? 12 : 10,
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.04)" },
        horzLines: { color: "rgba(255, 255, 255, 0.04)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        scaleMargins: { top: 0.1, bottom: showVolume ? 0.25 : 0.1 },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        timeVisible: interactive,
        secondsVisible: false,
      },
      crosshair: interactive
        ? { mode: 0 }
        : {
            mode: 0,
            vertLine: { color: "rgba(16, 185, 129, 0.5)", width: 1, style: 2 },
            horzLine: { color: "rgba(16, 185, 129, 0.5)", width: 1, style: 2 },
          },
      handleScroll: interactive,
      handleScale: interactive,
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
      priceLineVisible: !interactive,
      lastValueVisible: true,
    });
    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    if (showVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        color: "#3f3f46",
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
      });
      chart.priceScale("volume").applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeriesRef.current = volumeSeries;
    }
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
  }, [height, interactive, showVolume]);

  useEffect(() => {
    if (!candleSeriesRef.current) return;
    if (!candles || candles.length === 0) {
      candleSeriesRef.current.setData([]);
      volumeSeriesRef.current?.setData([]);
      return;
    }
    const sorted = [...candles].sort((a, b) => a.time - b.time);
    const candleData = sorted.map((c) => ({
      time: c.time as UTCTimestamp,
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
    }));
    candleSeriesRef.current.setData(candleData);
    if (showVolume && volumeSeriesRef.current) {
      const volumeData = sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        value: Number(c.volume),
        color:
          Number(c.close) >= Number(c.open)
            ? "rgba(16, 185, 129, 0.4)"
            : "rgba(239, 68, 68, 0.4)",
      }));
      volumeSeriesRef.current.setData(volumeData);
    }
    chartRef.current?.timeScale().fitContent();
  }, [candles, showVolume]);

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
