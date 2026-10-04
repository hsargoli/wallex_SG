"use client";

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
}

export function Sparkline({ data, width = 60, height = 24 }: SparklineProps) {
  if (!data || data.length < 2) {
    return <div style={{ width, height }} className="opacity-30" />;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const isUp = data[data.length - 1] >= data[0];
  const color = isUp ? "#10b981" : "#ef4444";

  return (
    <svg width={width} height={height} className="shrink-0" viewBox={`0 0 ${width} ${height}`}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
