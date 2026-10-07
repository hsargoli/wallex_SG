"use client";

import { useMemo } from "react";

export type Candle = { open: number; high: number; low: number; close: number };

const W = 960;
const H = 220;
const PAD = 18;

// عدد ثابت از روی ایندکس: رندر سرور و کلاینت یکسان می‌ماند (بدون Math.random)
const hash = (i: number, salt: number) =>
  ((((i + 1) * 2654435761 + salt * 40503) >>> 0) % 1000) / 1000;

export function BtcCandles({ candles, count = 48 }: { candles: Candle[]; count?: number }) {
  const view = useMemo(() => {
    const d = candles
      .slice(-count)
      .filter((k) => [k.open, k.high, k.low, k.close].every(Number.isFinite));
    if (d.length < 2) return null;
    const mn = Math.min(...d.map((k) => k.low));
    const mx = Math.max(...d.map((k) => k.high));
    const span = mx - mn || 1;
    const y = (v: number) => H - PAD - ((v - mn) / span) * (H - 2 * PAD);
    const cw = W / d.length;
    const last = d.length - 1;
    const rows = d.map((k, i) => {
      const up = k.close >= k.open;
      const mover = i !== last && hash(i, 1) < 0.5;
      const top = y(Math.max(k.open, k.close));
      const bot = y(Math.min(k.open, k.close));
      return {
        i,
        up,
        x: i * cw + cw / 2,
        yHi: y(k.high),
        yLo: y(k.low),
        top,
        h: Math.max(3, bot - top),
        cls:
          "wx-c" +
          (up ? "" : " wx-c--dn") +
          (i === last ? " wx-live" : mover ? (up ? " wx-mvu" : " wx-mvd") : ""),
        style: mover
          ? {
              animationDuration: (2.4 + hash(i, 2) * 2.6).toFixed(1) + "s",
              animationDelay: "-" + (hash(i, 3) * 6).toFixed(1) + "s",
            }
          : undefined,
      };
    });
    const lastRow = rows[last];
    return { cw, rows, lastY: y(d[last].close), lastUp: lastRow.up };
  }, [candles, count]);

  if (!view) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        داده‌ی کندل در دسترس نیست
      </p>
    );
  }

  return (
    <svg
      viewBox={"0 0 " + W + " " + H}
      role="img"
      aria-label="چارت کندلی ساده‌ی بیت‌کوین"
      className="wx-chart"
    >
      {[1, 2, 3].map((n) => (
        <line key={n} className="wx-gl" x1={0} x2={W} y1={(n * H) / 4} y2={(n * H) / 4} />
      ))}
      {view.rows.map((r) => (
        <g key={r.i} className={r.cls} style={r.style}>
          <line x1={r.x} x2={r.x} y1={r.yHi} y2={r.yLo} />
          <rect x={r.x - view.cw * 0.3} y={r.top} width={view.cw * 0.6} height={r.h} rx={2} />
        </g>
      ))}
      <line
        className="wx-gl"
        x1={0}
        x2={W}
        y1={view.lastY}
        y2={view.lastY}
        style={{ stroke: view.lastUp ? "var(--wx-up)" : "var(--wx-down)", strokeOpacity: 0.5 }}
      />
    </svg>
  );
}
