"use client";

import { useMemo } from "react";

export interface EquitySeries {
  name: string;
  data: number[];
  color: string;
  dashed?: boolean;
}

interface EquityChartProps {
  series: EquitySeries[];
  height?: number;
  width?: number;
  padding?: { top: number; right: number; bottom: number; left: number };
}

const DEFAULT_PADDING = { top: 12, right: 8, bottom: 28, left: 42 };

export function EquityChart({
  series,
  height = 220,
  width = 800,
  padding = DEFAULT_PADDING,
}: EquityChartProps) {
  const { paths, yTicks, yMin, yMax, xLen } = useMemo(() => {
    const valid = series.filter((s) => s.data.length > 0);
    if (valid.length === 0) {
      return { paths: [], yTicks: [], yMin: 0, yMax: 0, xLen: 0 };
    }
    const len = Math.min(...valid.map((s) => s.data.length));
    const truncated = valid.map((s) => ({ ...s, data: s.data.slice(0, len) }));
    const allValues = truncated.flatMap((s) => s.data);
    const rawMin = Math.min(...allValues);
    const rawMax = Math.max(...allValues);
    const margin = (rawMax - rawMin) * 0.05 || 1;
    const min = rawMin - margin;
    const max = rawMax + margin;
    const innerW = width - padding.left - padding.right;
    const innerH = height - padding.top - padding.bottom;
    const xAt = (i: number) => padding.left + (i / Math.max(len - 1, 1)) * innerW;
    const yAt = (v: number) => padding.top + (1 - (v - min) / (max - min)) * innerH;
    const paths = truncated.map((s) => ({
      name: s.name,
      color: s.color,
      dashed: s.dashed ?? false,
      d: s.data
        .map((v, i) => `${i === 0 ? "M" : "L"} ${xAt(i).toFixed(1)} ${yAt(v).toFixed(1)}`)
        .join(" "),
      last: s.data[s.data.length - 1],
    }));
    const nTicks = 5;
    const yTicks = Array.from({ length: nTicks }, (_, k) => {
      const v = min + ((max - min) * k) / (nTicks - 1);
      return { v, y: yAt(v) };
    });
    return { paths, yTicks, yMin: min, yMax: max, xLen: len };
  }, [series, width, height, padding]);

  if (paths.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-border/50 bg-card text-sm text-muted-foreground"
        style={{ height }}
      >
        داده‌ی نمودار موجود نیست
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto" dir="ltr">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        height={height}
        preserveAspectRatio="xMidYMid meet"
        className="text-muted-foreground"
      >
        {yTicks.map((t, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={t.y}
              y2={t.y}
              stroke="currentColor"
              strokeOpacity={0.08}
              strokeWidth={1}
            />
            <text
              x={padding.left - 6}
              y={t.y + 3}
              textAnchor="end"
              fontSize={10}
              fill="currentColor"
              fillOpacity={0.5}
            >
              {t.v.toFixed(1)}
            </text>
          </g>
        ))}

        {yMin <= 100 && yMax >= 100 && (
          <line
            x1={padding.left}
            x2={width - padding.right}
            y1={padding.top + (1 - (100 - yMin) / (yMax - yMin)) * (height - padding.top - padding.bottom)}
            y2={padding.top + (1 - (100 - yMin) / (yMax - yMin)) * (height - padding.top - padding.bottom)}
            stroke="currentColor"
            strokeOpacity={0.25}
            strokeDasharray="3 3"
            strokeWidth={1}
          />
        )}

        {paths.map((p) => (
          <path
            key={p.name}
            d={p.d}
            fill="none"
            stroke={p.color}
            strokeWidth={p.dashed ? 1.5 : 2}
            strokeDasharray={p.dashed ? "5 4" : undefined}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}

        <text x={padding.left} y={height - 8} textAnchor="start" fontSize={10} fill="currentColor" fillOpacity={0.5}>
          شروع
        </text>
        <text x={width - padding.right} y={height - 8} textAnchor="end" fontSize={10} fill="currentColor" fillOpacity={0.5}>
          پایان ({xLen} کندل)
        </text>
      </svg>

      <div className="mt-2 flex flex-wrap items-center gap-4 px-2 text-xs" dir="rtl">
        {paths.map((p) => (
          <div key={p.name} className="flex items-center gap-2">
            <svg width={20} height={8}>
              <line x1={0} x2={20} y1={4} y2={4} stroke={p.color} strokeWidth={2} strokeDasharray={p.dashed ? "4 3" : undefined} />
            </svg>
            <span className="text-muted-foreground">{p.name}</span>
            <span className="font-mono font-bold" style={{ color: p.color }}>
              {p.last.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
