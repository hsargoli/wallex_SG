"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

type SignalItem = {
  symbol: string;
  signal: string;
  current_price?: string;
  change_1h?: number | null;
};

const SIGNAL_COLORS: Record<string, string> = {
  buy: "#10b981",
  sell: "#ef4444",
  hold: "#71717a",
  none: "#f59e0b",
};

const REVEAL_INTERVAL_MS = 100;
const MAX_STARS = 50;

interface Star {
  x: number;
  y: number;
  size: number;
  color: string;
  symbol: string;
  signal: string;
}

interface Props {
  signals: SignalItem[];
  isLoading: boolean;
}

export function CosmosCanvas({ signals, isLoading }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const [stars, setStars] = useState<Star[]>([]);
  const [visible, setVisible] = useState(0);
  const [dims, setDims] = useState({ w: 0, h: 0 });

  // Track container size
  useEffect(() => {
    const c = containerRef.current;
    if (!c) return;
    const update = () => setDims({ w: c.clientWidth, h: c.clientHeight });
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Generate stars once signals + dims are ready
  useEffect(() => {
    if (signals.length === 0 || dims.w === 0) return;
    const pad = 30;
    const limited = signals.slice(0, MAX_STARS);
    const newStars: Star[] = limited.map((s) => {
      const price = Number(s.current_price) || 1;
      const logSize = Math.min(7, Math.max(0, Math.log10(price + 1)));
      return {
        x: Math.random() * (dims.w - pad * 2) + pad,
        y: Math.random() * (dims.h - pad * 2) + pad,
        size: 5 + logSize * 0.8,
        color: SIGNAL_COLORS[s.signal] ?? SIGNAL_COLORS.none,
        symbol: s.symbol,
        signal: s.signal,
      };
    });
    setStars(newStars);
    setVisible(0);
  }, [signals, dims.w, dims.h]);

  // Progressive reveal
  useEffect(() => {
    if (stars.length === 0) return;
    let cur = 0;
    setVisible(0);
    const t = setInterval(() => {
      cur += 1;
      if (cur >= stars.length) {
        clearInterval(t);
        setVisible(stars.length);
        return;
      }
      setVisible(cur);
    }, REVEAL_INTERVAL_MS);
    return () => clearInterval(t);
  }, [stars]);

  // Render
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || dims.w === 0) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = dims.w * dpr;
    canvas.height = dims.h * dpr;
    canvas.style.width = `${dims.w}px`;
    canvas.style.height = `${dims.h}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Background
    ctx.fillStyle = "#050507";
    ctx.fillRect(0, 0, dims.w, dims.h);

    // Static decorative stars (deterministic)
    ctx.fillStyle = "rgba(255,255,255,0.12)";
    for (let i = 0; i < 100; i++) {
      const x = ((i * 73) % dims.w) + (i % 7) * 0.5;
      const y = ((i * 137) % dims.h) + (i % 5) * 0.5;
      ctx.beginPath();
      ctx.arc(x, y, 0.6, 0, Math.PI * 2);
      ctx.fill();
    }

    // Main stars (progressive)
    const count = Math.min(visible, stars.length);
    for (let i = 0; i < count; i++) {
      const s = stars[i];
      ctx.save();
      ctx.shadowColor = s.color;
      ctx.shadowBlur = s.size * 3;
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      // Bright core
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(s.x, s.y, Math.max(1, s.size * 0.35), 0, Math.PI * 2);
      ctx.fill();
    }
  }, [stars, visible, dims]);

  // Click: navigate to /signals/{symbol}
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const count = Math.min(visible, stars.length);
      for (let i = count - 1; i >= 0; i--) {
        const s = stars[i];
        if (Math.hypot(s.x - x, s.y - y) <= s.size + 6) {
          router.push(`/signals/${s.symbol}`);
          return;
        }
      }
    },
    [stars, visible, router],
  );

  return (
    <div ref={containerRef} className="relative h-full w-full">
      <canvas
        ref={canvasRef}
        onClick={handleClick}
        className="block h-full w-full cursor-crosshair"
      />

      {/* HUD overlay */}
      <div className="pointer-events-none absolute inset-0 flex flex-col">
        <div className="flex items-start justify-between p-4 text-white/80">
          <div>
            <h1 className="text-lg font-bold">کیهان بازار</h1>
            <p className="text-xs text-white/50">
              {Math.min(visible, stars.length)} / {stars.length} ستاره
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-[10px]">
            {(["buy", "sell", "hold", "none"] as const).map((k) => (
              <span key={k} className="flex items-center gap-1">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ background: SIGNAL_COLORS[k] }}
                />
                {k === "buy" && "خرید"}
                {k === "sell" && "فروش"}
                {k === "hold" && "بی‌طرف"}
                {k === "none" && "آماده‌سازی"}
              </span>
            ))}
          </div>
        </div>

        {isLoading && stars.length === 0 && (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-sm text-white/60">
              در حال دریافت داده‌ی کهکشان...
            </p>
          </div>
        )}

        {!isLoading && stars.length === 0 && (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-sm text-white/60">
              داده‌ای برای نمایش نیست.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
