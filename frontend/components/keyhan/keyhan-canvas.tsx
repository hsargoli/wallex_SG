"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { formatPrice } from "@/lib/format";

type SignalItem = {
  symbol: string;
  signal: string;
  current_price?: string;
  change_1h?: number | null;
  sparkline?: number[];
};

const SIGNAL_COLORS: Record<string, string> = {
  buy: "#10b981",
  sell: "#ef4444",
  hold: "#c7c7cd",
  none: "#f59e0b",
};

const SIGNAL_LABELS: Record<string, string> = {
  buy: "خرید",
  sell: "فروش",
  hold: "بی‌طرف",
  none: "بدون سیگنال",
};

const REVEAL_INTERVAL_MS = 80;
const MAX_STARS = 50;
const TARGET_FPS = 30;
const HIT_RADIUS_PAD = 8;

const MIN_SIZE = 1.5;
const MAX_SIZE = 22.0; // significantly larger for giants

interface Star {
  x: number;
  y: number;
  size: number;
  baseColor: string;
  symbol: string;
  signal: string;
  price: number;
  vol: number;
  change1h: number | null;
  seed: number;
  isGiant: boolean;
}

interface Props {
  signals: SignalItem[];
  volumeMap: Record<string, number>;
  isLoading: boolean;
}

export function KeyhanCanvas({ signals, volumeMap, isLoading }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const [stars, setStars] = useState<Star[]>([]);
  const [visible, setVisible] = useState(0);
  const [dims, setDims] = useState({ w: 0, h: 0 });
  const [hover, setHover] = useState<{ star: Star; mx: number; my: number } | null>(null);

  // Refs for animation loop
  const starsRef = useRef<Star[]>([]);
  const visibleRef = useRef(0);
  const dimsRef = useRef({ w: 0, h: 0 });
  const hoveredRef = useRef<Star | null>(null);

  useEffect(() => { starsRef.current = stars; }, [stars]);
  useEffect(() => { visibleRef.current = visible; }, [visible]);
  useEffect(() => { dimsRef.current = dims; }, [dims]);
  useEffect(() => { hoveredRef.current = hover?.star ?? null; }, [hover]);

  // Track container size
  useEffect(() => {
    const c = containerRef.current;
    if (!c) return;
    const update = () => setDims({ w: c.clientWidth, h: c.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(c);
    return () => ro.disconnect();
  }, []);

  // Generate fixed background stars (outside main loop for performance)
  const bgStars = useMemo(() => {
    const arr = [];
    const colors = ["#ffffff", "#a5b4fc", "#fde047", "#e0e7ff", "#fca5a5"];
    for (let i = 0; i < 400; i++) {
      arr.push({
        x: Math.random(),
        y: Math.random(),
        size: Math.random() * 1.5 + 0.2,
        color: colors[Math.floor(Math.random() * colors.length)],
        phase: Math.random() * Math.PI * 2,
        speed: 0.3 + Math.random() * 1.5,
        opacity: Math.random() * 0.6 + 0.2,
      });
    }
    return arr;
  }, []);

  // Build main stars once data ready
  useEffect(() => {
    if (signals.length === 0 || dims.w === 0) return;
    const pad = 80; // More padding so big stars don't clip
    const limited = signals.slice(0, MAX_STARS);

    // Volume range for normalization
    const vols = limited.map((s) => volumeMap[s.symbol] ?? 0);
    const maxVol = Math.max(...vols, 1);
    const minVol = Math.min(...vols);

    // Find true top 3 by volume (independent of API error sorting)
    const sortedByVol = [...limited].sort(
      (a, b) => (volumeMap[b.symbol] ?? 0) - (volumeMap[a.symbol] ?? 0)
    );
    const top3Symbols = new Set(sortedByVol.slice(0, 3).map((s) => s.symbol));

    const newStars: Star[] = limited.map((s, i) => {
      const price = Number(s.current_price) || 1;
      const vol = volumeMap[s.symbol] ?? 0;
      // Steeper curve: small vols stay small, big vols get huge
      const ratio = maxVol > minVol ? (vol - minVol) / (maxVol - minVol) : 1;
      let size = MIN_SIZE + Math.pow(ratio, 1.8) * (MAX_SIZE - MIN_SIZE);
      
      // BTC Anchor: never let it be a tiny dot, even if volume dips
      if (s.symbol === "BTCTMN") {
        size = Math.max(size, 10.0);
      }
      
      return {
        x: Math.random() * (dims.w - pad * 2) + pad,
        y: Math.random() * (dims.h - pad * 2) + pad,
        size,
        baseColor: SIGNAL_COLORS[s.signal] ?? SIGNAL_COLORS.none,
        symbol: s.symbol,
        signal: s.signal,
        price,
        vol,
        change1h: s.change_1h ?? null,
        seed: Math.random() * 1000 + i,
        isGiant: top3Symbols.has(s.symbol),
      };
    });
    
    // Draw small stars first, giants last (giants always on top)
    newStars.sort((a, b) => a.size - b.size);
    
    setStars(newStars);
    setVisible(0);
  }, [signals, volumeMap, dims.w, dims.h]);

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

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let raf = 0;
    let lastFrame = 0;
    const frameInterval = 1000 / TARGET_FPS;

    const drawStar = (
      ctx: CanvasRenderingContext2D,
      star: Star,
      t: number,
      isHovered: boolean,
    ) => {
      const { x, y, size, baseColor, isGiant, symbol } = star;
      
      const baseTwinkle = 0.65 + 0.35 * Math.sin(t * 0.0012 * (1 + (star.seed % 3) * 0.4) + star.seed);
      
      // Damping: Larger stars are dimmer/softer so they don't blind the user
      let brightnessFactor = 1.0;
      if (size > 10) {
        brightnessFactor = Math.max(0.35, 1.0 - (size - 10) * 0.045);
      }
      const twinkle = baseTwinkle * brightnessFactor;

      // Orbit + Label for Giants AND Bitcoin (always)
      const isBTC = symbol === "BTCTMN";
      if (isGiant || isBTC) {
        const orbitR = size * 6;
        ctx.strokeStyle = hexToRgba(baseColor, 0.25);
        ctx.lineWidth = 0.8;
        ctx.setLineDash([3, 5]);
        ctx.beginPath();
        ctx.arc(x, y, orbitR, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Small label under giant stars
        ctx.fillStyle = `rgba(255,255,255,0.95)`;
        ctx.font = "bold 12px monospace";
        ctx.textAlign = "center";
        ctx.shadowColor = "black";
        ctx.shadowBlur = 4;
        ctx.fillText(symbol.replace("TMN", ""), x, y + orbitR + 16);
        ctx.shadowBlur = 0; // reset
      }

      // Outer glow (very large for giants)
      const glowRadius = size * (isHovered ? 7 : 5) * (0.85 + twinkle * 0.3);
      const grad = ctx.createRadialGradient(x, y, 0, x, y, glowRadius);
      grad.addColorStop(0, baseColor);
      grad.addColorStop(0.2, hexToRgba(baseColor, 0.6 * twinkle));
      grad.addColorStop(0.5, hexToRgba(baseColor, 0.15 * twinkle));
      grad.addColorStop(1, hexToRgba(baseColor, 0));
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
      ctx.fill();

      // Diffraction spikes (longer for giants)
      const rayLen = size * (isHovered ? 8 : 6) * (0.75 + twinkle * 0.4);
      ctx.strokeStyle = hexToRgba(baseColor, 0.65 * twinkle);
      ctx.lineWidth = 0.8 + (size / MAX_SIZE); // Thicker spikes for giants
      ctx.beginPath();
      ctx.moveTo(x - rayLen, y);
      ctx.lineTo(x + rayLen, y);
      ctx.moveTo(x, y - rayLen);
      ctx.lineTo(x, y + rayLen);
      ctx.stroke();

      // Short diagonal spikes
      const diagLen = rayLen * 0.45;
      ctx.strokeStyle = hexToRgba(baseColor, 0.4 * twinkle);
      ctx.lineWidth = 0.5 + (size / MAX_SIZE) * 0.5;
      ctx.beginPath();
      ctx.moveTo(x - diagLen, y - diagLen);
      ctx.lineTo(x + diagLen, y + diagLen);
      ctx.moveTo(x + diagLen, y - diagLen);
      ctx.lineTo(x - diagLen, y + diagLen);
      ctx.stroke();

      // Bright core (damped for giants)
      const coreOpacity = Math.max(0.4, (0.85 + baseTwinkle * 0.15) * Math.max(0.5, brightnessFactor));
      ctx.fillStyle = `rgba(255,255,255,${coreOpacity})`;
      ctx.beginPath();
      ctx.arc(x, y, Math.max(1, size * 0.45), 0, Math.PI * 2);
      ctx.fill();
    };

    const draw = (t: number) => {
      const { w, h } = dimsRef.current;
      if (w === 0) return;
      const dpr = window.devicePixelRatio || 1;
      if (canvas.width !== Math.round(w * dpr)) {
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
        canvas.style.width = `${w}px`;
        canvas.style.height = `${h}px`;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Deep space background
      ctx.fillStyle = "#050507";
      ctx.fillRect(0, 0, w, h);

      // Nebulae
      const nebulae = [
        { x: 0.18, y: 0.28, r: 0.45, color: "rgba(90, 60, 180, 0.12)" },
        { x: 0.78, y: 0.72, r: 0.55, color: "rgba(40, 90, 200, 0.09)" },
        { x: 0.5, y: 0.5, r: 0.6, color: "rgba(150, 80, 200, 0.06)" },
      ];
      for (const n of nebulae) {
        const grad = ctx.createRadialGradient(
          w * n.x, h * n.y, 0, w * n.x, h * n.y, Math.max(w, h) * n.r,
        );
        grad.addColorStop(0, n.color);
        grad.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }

      // Realistic background stars
      for (const s of bgStars) {
        const tw = 0.5 + 0.5 * Math.sin(t * 0.001 * s.speed + s.phase);
        ctx.fillStyle = hexToRgba(s.color, s.opacity * (0.4 + tw * 0.6));
        ctx.beginPath();
        ctx.arc(s.x * w, s.y * h, s.size, 0, Math.PI * 2);
        ctx.fill();
      }

      // Main stars
      const starsArr = starsRef.current;
      const vis = visibleRef.current;
      const hovered = hoveredRef.current;
      const count = Math.min(vis, starsArr.length);
      for (let i = 0; i < count; i++) {
        drawStar(ctx, starsArr[i], t, starsArr[i] === hovered);
      }
    };

    const loop = (t: number) => {
      raf = requestAnimationFrame(loop);
      if (t - lastFrame < frameInterval) return;
      lastFrame = t;
      draw(t);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [bgStars]);

  const findStarAt = useCallback((mx: number, my: number): Star | null => {
    const starsArr = starsRef.current;
    const vis = visibleRef.current;
    const count = Math.min(vis, starsArr.length);
    let best: Star | null = null;
    let bestDist = Infinity;
    // Check from top (drawn last) to bottom
    for (let i = count - 1; i >= 0; i--) {
      const s = starsArr[i];
      const d = Math.hypot(s.x - mx, s.y - my);
      // Increase hit radius for bigger stars
      const hitR = Math.max(s.size * 3, HIT_RADIUS_PAD);
      if (d <= hitR && d < bestDist) {
        best = s;
        bestDist = d;
      }
    }
    return best;
  }, []);

  const onMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const s = findStarAt(mx, my);
    if (s) {
      setHover({ star: s, mx, my });
      canvas.style.cursor = "pointer";
    } else {
      setHover(null);
      canvas.style.cursor = "crosshair";
    }
  };

  const onMouseLeave = () => {
    setHover(null);
    const canvas = canvasRef.current;
    if (canvas) canvas.style.cursor = "crosshair";
  };

  const onClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const s = findStarAt(e.clientX - rect.left, e.clientY - rect.top);
    if (s) router.push(`/signals/${s.symbol}`);
  };

  const hoverLeft = hover ? hover.mx + 14 : 0;
  const hoverTop = hover ? hover.my - 8 : 0;

  return (
    <div ref={containerRef} className="relative h-full w-full">
      <canvas
        ref={canvasRef}
        onMouseMove={onMouseMove}
        onMouseLeave={onMouseLeave}
        onClick={onClick}
        className="block h-full w-full"
        style={{ cursor: "crosshair" }}
      />

      {/* HUD overlay */}
      <div className="pointer-events-none absolute inset-0 flex flex-col">
        <div className="flex items-start justify-between p-4 text-white/80">
          <div>
            <h1 className="text-lg font-bold">کیهان بازار</h1>
            <p className="text-xs text-white/50">
              {Math.min(visible, stars.length)} / {stars.length} ستاره
              <span className="ml-3 text-[10px] text-white/40">
                (اندازه ستاره = حجم معاملات ۲۴ ساعته)
              </span>
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-[10px]">
            {(["buy", "sell", "hold", "none"] as const).map((k) => (
              <span key={k} className="flex items-center gap-1">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ background: SIGNAL_COLORS[k] }}
                />
                {SIGNAL_LABELS[k]}
              </span>
            ))}
          </div>
        </div>

        {isLoading && stars.length === 0 && (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-sm text-white/60">در حال دریافت داده‌ی کهکشان...</p>
          </div>
        )}

        {!isLoading && stars.length === 0 && (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-sm text-white/60">داده‌ای برای نمایش نیست.</p>
          </div>
        )}
      </div>

      {/* Tooltip */}
      {hover && (
        <div
          className="pointer-events-none absolute z-20 min-w-[160px] rounded-lg border border-white/15 bg-black/90 px-3 py-2 text-[11px] text-white shadow-2xl backdrop-blur-sm"
          style={{ left: hoverLeft, top: hoverTop }}
        >
          <div className="flex items-center justify-between gap-3">
            <span className="font-mono text-xs font-bold">{hover.star.symbol}</span>
            <span
              className="rounded-full px-1.5 py-0.5 text-[9px]"
              style={{
                background: hexToRgba(hover.star.baseColor, 0.18),
                color: hover.star.baseColor,
              }}
            >
              {SIGNAL_LABELS[hover.star.signal] ?? "—"}
            </span>
          </div>
          <div className="mt-1 flex items-center justify-between gap-3 font-mono text-[10px] text-white/70">
            <span>{formatPrice(hover.star.price)}</span>
            {hover.star.change1h !== null && (
              <span
                className={
                  hover.star.change1h >= 0 ? "text-emerald-400" : "text-red-400"
                }
              >
                {hover.star.change1h >= 0 ? "▲" : "▼"}{" "}
                {Math.abs(hover.star.change1h).toFixed(2)}%
              </span>
            )}
          </div>
          <div className="mt-1.5 flex items-center justify-between gap-3 font-mono text-[10px] text-white/60 border-t border-white/10 pt-1">
            <span>حجم ۲۴س:</span>
            <span>{formatVolume(hover.star.vol)}</span>
          </div>
          <div className="mt-1 text-[9px] text-white/40">تغییرات ۱ ساعت اخیر</div>
        </div>
      )}
    </div>
  );
}

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function formatVolume(v: number): string {
  if (!v) return "—";
  if (v >= 1e9) return `${(v / 1e9).toFixed(2)}B TMN`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M TMN`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(2)}K TMN`;
  return `${v.toFixed(0)} TMN`;
}
