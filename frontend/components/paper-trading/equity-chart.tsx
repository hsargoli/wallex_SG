"use client";

import { useEffect, useRef } from "react";
import {
  AreaSeries,
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

interface EquityPoint {
  time: number;
  capital: number;
}

interface Props {
  data: EquityPoint[];
  initialCapital: number;
  height?: number;
}

export function PaperEquityChart({ data, initialCapital, height = 280 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "Vazirmatn, system-ui, sans-serif",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.03)" },
        horzLines: { color: "rgba(255, 255, 255, 0.03)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.05)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.05)",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: false,
      handleScale: false,
      width: containerRef.current.clientWidth,
      height,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: "#10b981",
      topColor: "rgba(16, 185, 129, 0.4)",
      bottomColor: "rgba(16, 185, 129, 0.05)",
      lineWidth: 2,
      priceLineVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    const observer = new ResizeObserver(handleResize);
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current) return;

    // اگه داده خالی، initial capital رو نمایش بده
    const points = data.length > 0 
      ? data 
      : [{ time: Math.floor(Date.now() / 1000), capital: initialCapital }];

    const sorted = [...points].sort((a, b) => a.time - b.time);

    const chartData = sorted.map((p) => ({
      time: p.time as UTCTimestamp,
      value: p.capital,
    }));

    seriesRef.current.setData(chartData);
    chartRef.current?.timeScale().fitContent();
  }, [data, initialCapital]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className="h-5 w-5 text-emerald-400" />
          منحنی سرمایه (Equity Curve)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative w-full" dir="ltr">
          <div ref={containerRef} className="w-full" />
        </div>
        {data.length === 0 && (
          <p className="mt-3 text-center text-xs text-muted-foreground">
            هنوز تریدی ثبت نشده — نمودار پس از اولین ترید نمایش داده می‌شود
          </p>
        )}
      </CardContent>
    </Card>
  );
}
