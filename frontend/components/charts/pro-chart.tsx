"use client";

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { type Candle } from "@/lib/api";
import { cn } from "@/lib/utils";
import { type LegendData } from "./chart-legend";

interface ProChartProps {
  candles: Candle[];
  indicators?: {
    ema9?: (string | null)[];
    ema21?: (string | null)[];
    ema50?: (string | null)[];
    bbUpper?: (string | null)[];
    bbMiddle?: (string | null)[];
    bbLower?: (string | null)[];
    rsi14?: (string | null)[];
    macd?: (string | null)[];
    macdSignal?: (string | null)[];
    macdHist?: (string | null)[];
  };
  height?: number;
  showVolume?: boolean;
  showEMA?: boolean;
  showBB?: boolean;
  showRSI?: boolean;
  showMACD?: boolean;
  loading?: boolean;
  onCrosshairMove?: (data: LegendData | undefined) => void;
}

export function ProChart({
  candles,
  indicators,
  height = 500,
  showVolume = true,
  showEMA = true,
  showBB = false,
  showRSI = false,
  showMACD = false,
  loading = false,
  onCrosshairMove,
}: ProChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const ema9Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const ema21Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbMiddleRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<"Line"> | null>(null);
  const rsiRef = useRef<ISeriesApi<"Line"> | null>(null);
  const rsi70Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const rsi30Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const macdLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdSignalRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdHistRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  // داده‌های جاری برای crosshair
  const dataRef = useRef<{
    sorted: Candle[];
    indicators?: ProChartProps["indicators"];
  }>({ sorted: [] });

  // callback ref — بدون نیاز به re-mount
  const cbRef = useRef(onCrosshairMove);
  cbRef.current = onCrosshairMove;

  // آخرین داده‌ی crosshair — برای جلوگیری از fire تکراری
  const lastLegendRef = useRef<string>("");

  // Create chart + series
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
        scaleMargins: { top: 0.1, bottom: showVolume ? 0.25 : 0.1 },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.06)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: { mode: 0 },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
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

    candleRef.current = candleSeries;

    if (showVolume) {
      const volSeries = chart.addSeries(HistogramSeries, {
        color: "#3f3f46",
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
      });
      chart.priceScale("volume").applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volRef.current = volSeries;
    }

    if (showEMA) {
      ema9Ref.current = chart.addSeries(LineSeries, {
        color: "#10b981",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "EMA 9",
      });
      ema21Ref.current = chart.addSeries(LineSeries, {
        color: "#f59e0b",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "EMA 21",
      });
    }

    if (showBB) {
      bbUpperRef.current = chart.addSeries(LineSeries, {
        color: "#a855f7",
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      bbMiddleRef.current = chart.addSeries(LineSeries, {
        color: "#a855f7",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      bbLowerRef.current = chart.addSeries(LineSeries, {
        color: "#a855f7",
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
    }

    // ─── RSI Pane ───
    if (showRSI) {
      const rsiPane = chart.addPane(false);
      rsiPane.setHeight(120);

      rsiRef.current = chart.addSeries(
        LineSeries,
        {
          color: "#a855f7",
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: true,
          title: "RSI",
        },
        rsiPane.paneIndex(),
      );

      rsi70Ref.current = chart.addSeries(
        LineSeries,
        {
          color: "rgba(239, 68, 68, 0.5)",
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        },
        rsiPane.paneIndex(),
      );

      rsi30Ref.current = chart.addSeries(
        LineSeries,
        {
          color: "rgba(16, 185, 129, 0.5)",
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        },
        rsiPane.paneIndex(),
      );

    }

    // ─── MACD Pane ───
    if (showMACD) {
      const macdPane = chart.addPane(false);
      macdPane.setHeight(120);

      macdHistRef.current = chart.addSeries(
        HistogramSeries,
        {
          priceLineVisible: false,
          lastValueVisible: false,
        },
        macdPane.paneIndex(),
      );

      macdLineRef.current = chart.addSeries(
        LineSeries,
        {
          color: "#10b981",
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
          title: "MACD",
        },
        macdPane.paneIndex(),
      );

      macdSignalRef.current = chart.addSeries(
        LineSeries,
        {
          color: "#f59e0b",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          title: "Signal",
        },
        macdPane.paneIndex(),
      );
    }

    chartRef.current = chart;

    // ─── Crosshair subscription ───
    chart.subscribeCrosshairMove((param) => {
      const cb = cbRef.current;
      if (!cb) return;

      // وقتی موس بیرونه یا داده‌ای نیست → undefined
      if (
        !param.time ||
        !param.point ||
        param.point.x < 0 ||
        param.point.y < 0
      ) {
        if (lastLegendRef.current !== "undefined") {
          lastLegendRef.current = "undefined";
          cb(undefined);
        }
        return;
      }

      const { sorted, indicators } = dataRef.current;
      if (sorted.length === 0) {
        cb(undefined);
        return;
      }

      // پیدا کردن ایندکس کندل از روی time
      const idx = sorted.findIndex((c) => c.time === (param.time as number));
      if (idx < 0) {
        cb(undefined);
        return;
      }

      const c = sorted[idx];
      const prev = idx > 0 ? sorted[idx - 1] : null;
      const open = Number(c.open);
      const close = Number(c.close);
      const changePct = prev
        ? ((close - Number(prev.close)) / Number(prev.close)) * 100
        : 0;

      const n = (v?: string | null): number | null => {
        if (v === null || v === undefined) return null;
        const x = Number(v);
        return Number.isFinite(x) ? x : null;
      };

      const payload = {
        time: c.time,
        open,
        high: Number(c.high),
        low: Number(c.low),
        close,
        changePct,
        ema9: n(indicators?.ema9?.[idx]),
        ema21: n(indicators?.ema21?.[idx]),
        bbUpper: n(indicators?.bbUpper?.[idx]),
        bbMiddle: n(indicators?.bbMiddle?.[idx]),
        bbLower: n(indicators?.bbLower?.[idx]),
        rsi: n(indicators?.rsi14?.[idx]),
        macd: n(indicators?.macd?.[idx]),
        macdSignal: n(indicators?.macdSignal?.[idx]),
        macdHist: n(indicators?.macdHist?.[idx]),
      };

      // فقط اگه واقعاً تغییر کرده، fire کن
      const key = JSON.stringify(payload);
      if (key === lastLegendRef.current) return;
      lastLegendRef.current = key;
      cb(payload);
    });

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
      candleRef.current = null;
      volRef.current = null;
      ema9Ref.current = null;
      ema21Ref.current = null;
      bbUpperRef.current = null;
      bbMiddleRef.current = null;
      bbLowerRef.current = null;
      rsiRef.current = null;
      rsi70Ref.current = null;
      rsi30Ref.current = null;
      macdLineRef.current = null;
      macdSignalRef.current = null;
      macdHistRef.current = null;
    };
  }, [height, showVolume, showEMA, showBB, showRSI, showMACD]);

  // Update data
  useEffect(() => {
    if (!candleRef.current || !candles || candles.length === 0) return;

    const sorted = [...candles].sort((a, b) => a.time - b.time);

    // ذخیره برای crosshair
    dataRef.current = { sorted, indicators };

    candleRef.current.setData(
      sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        open: Number(c.open),
        high: Number(c.high),
        low: Number(c.low),
        close: Number(c.close),
      })),
    );

    if (showVolume && volRef.current) {
      volRef.current.setData(
        sorted.map((c) => ({
          time: c.time as UTCTimestamp,
          value: Number(c.volume),
          color:
            Number(c.close) >= Number(c.open)
              ? "rgba(16, 185, 129, 0.3)"
              : "rgba(239, 68, 68, 0.3)",
        })),
      );
    }

    // Map indicators (they have same length as candles)
    const mapLine = (arr?: (string | null)[]) => {
      if (!arr || arr.length !== sorted.length) return [];
      return arr
        .map((v, i) => {
          if (v === null || v === undefined) return null;
          return { time: sorted[i].time as UTCTimestamp, value: Number(v) };
        })
        .filter((p): p is { time: UTCTimestamp; value: number } => p !== null);
    };

    if (showEMA) {
      ema9Ref.current?.setData(mapLine(indicators?.ema9));
      ema21Ref.current?.setData(mapLine(indicators?.ema21));
    }

    if (showBB) {
      bbUpperRef.current?.setData(mapLine(indicators?.bbUpper));
      bbMiddleRef.current?.setData(mapLine(indicators?.bbMiddle));
      bbLowerRef.current?.setData(mapLine(indicators?.bbLower));
    }

    if (showRSI) {
      rsiRef.current?.setData(mapLine(indicators?.rsi14));
      // خطوط 70 و 30 ثابت
      const rsi70Data = sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        value: 70,
      }));
      const rsi30Data = sorted.map((c) => ({
        time: c.time as UTCTimestamp,
        value: 30,
      }));
      rsi70Ref.current?.setData(rsi70Data);
      rsi30Ref.current?.setData(rsi30Data);
    }

    if (showMACD) {
      macdLineRef.current?.setData(mapLine(indicators?.macd));
      macdSignalRef.current?.setData(mapLine(indicators?.macdSignal));

      // MACD histogram — رنگ‌بندی بر اساس مثبت/منفی
      if (indicators?.macdHist && indicators.macdHist.length === sorted.length) {
        const histData = indicators.macdHist
          .map((v, i) => {
            if (v === null || v === undefined) return null;
            const val = Number(v);
            return {
              time: sorted[i].time as UTCTimestamp,
              value: val,
              color: val >= 0 ? "rgba(16, 185, 129, 0.5)" : "rgba(239, 68, 68, 0.5)",
            };
          })
          .filter(
            (p): p is { time: UTCTimestamp; value: number; color: string } =>
              p !== null,
          );
        macdHistRef.current?.setData(histData);
      }
    }

    chartRef.current?.timeScale().fitContent();
  }, [candles, indicators, showVolume, showEMA, showBB, showRSI, showMACD]);

  return (
    <div className="relative w-full" dir="ltr">
      <div ref={containerRef} className="w-full" />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="text-sm text-muted-foreground">
            در حال بارگذاری...
          </div>
        </div>
      )}
    </div>
  );
}
