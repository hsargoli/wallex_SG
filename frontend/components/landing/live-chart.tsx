"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { TrendingUp, TrendingDown, Sparkles, Diamond } from "lucide-react";

type Candle = { id: number; o: number; c: number; h: number; l: number; v: number };

const SPACING = 45, W = 22, DX = 5, DY = 4;
const MIN_P = 75, MAX_P = 135;
const TOP = 60, BOTTOM = 290, H = BOTTOM - TOP;
const START_X = 40;
const yFor = (p: number) =>
  BOTTOM - ((Math.max(MIN_P, Math.min(MAX_P, p)) - MIN_P) / (MAX_P - MIN_P)) * H;

let idc = 1000;
let tick = 0;

function candleAt(i: number, phase: number): Candle {
  const p = i + phase;
  const trend = i * 0.85;
  const wave = Math.sin(p * 0.65) * 9 + Math.cos(p * 1.15) * 5;
  const noise = (Math.random() - 0.5) * 3.5;
  const c = 100 + trend + wave + noise;
  const prevTrend = (i - 1) * 0.85;
  const prevWave = i === 0 ? 0 : Math.sin((p - 1) * 0.65) * 9 + Math.cos((p - 1) * 1.15) * 5;
  const o = i === 0 ? c - 1.5 : 100 + prevTrend + prevWave;
  const hi = Math.max(o, c) + 1.5 + Math.random() * 5;
  const lo = Math.min(o, c) - 1.5 - Math.random() * 5;
  const v = 16 + Math.random() * 50;
  return { id: ++idc, o, c, h: hi, l: lo, v };
}

function seed(phase: number): Candle[] {
  const out: Candle[] = [];
  for (let i = 0; i < 16; i++) {
    out.push(candleAt(i, phase));
    tick = i;
  }
  return out;
}

const UP   = { front: "#10b981", side: "#047857", top: "#34d399", wick: "#10b981" };
const DOWN = { front: "#f43f5e", side: "#9f1239", top: "#fb7185", wick: "#f43f5e" };

/* ── ارزهای SarvBots ── */
type SymKey = "MATMN" | "SCTMN";

type SymConf = {
  key: SymKey;
  fa: string;
  faFull: string;
  en: string;
  icon: "sparkles" | "diamond";
  basePrice: number;
  volRange: number;
  minTick: number;
  maxTick: number;
  seedPhase: number;
};

const SYMBOLS: Record<SymKey, SymConf> = {
  MATMN: {
    key: "MATMN",
    fa: "ما",
    faFull: "اسمارت کوین",
    en: "MA/TMN",
    icon: "sparkles",
    basePrice: 15_800,
    volRange: 240,
    minTick: 12_000,
    maxTick: 22_000,
    seedPhase: 0,
  },
  SCTMN: {
    key: "SCTMN",
    fa: "اسمارت کوین",
    faFull: "توکن SarvBots",
    en: "SC/TMN",
    icon: "diamond",
    basePrice: 42_500,
    volRange: 780,
    minTick: 35_000,
    maxTick: 56_000,
    seedPhase: 500,
  },
};

const IconOf = ({ kind, className }: { kind: SymConf["icon"]; className?: string }) =>
  kind === "sparkles"
    ? <Sparkles className={className} />
    : <Diamond className={className} />;

export function LiveChart({ className }: { className?: string }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const [sym, setSym] = useState<SymKey>("MATMN");
  const conf = SYMBOLS[sym];

  const [candles, setCandles] = useState<Candle[]>(() => seed(SYMBOLS.MATMN.seedPhase));
  const [price, setPrice] = useState({ p: SYMBOLS.MATMN.basePrice, ch: 1.24, up: true, k: 0 });
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const wrapRef = useRef<HTMLDivElement>(null);

  const switchSym = (next: SymKey) => {
    if (next === sym) return;
    setSym(next);
    const c = SYMBOLS[next];
    setCandles(seed(c.seedPhase));
    setPrice({ p: c.basePrice, ch: 0.5, up: true, k: 0 });
  };

  useEffect(() => {
    const t = setInterval(() => {
      tick++;
      setCandles(prev => [...prev.slice(1), candleAt(tick, conf.seedPhase)]);
    }, 1800);
  // جلوگیری از خطای Hydration در SSR
return () => clearInterval(t);
  }, [conf.seedPhase]);

  useEffect(() => {
    const t = setInterval(() => {
      setPrice(prev => {
        const d = (Math.random() - 0.45) * conf.volRange;
        const p = Math.max(conf.minTick, Math.min(conf.maxTick, prev.p + d));
        return { p, ch: Math.abs((d / prev.p) * 100), up: d >= 0, k: prev.k + 1 };
      });
    }, 1500);
    return () => clearInterval(t);
  }, [conf]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const mv = (e: MouseEvent) => {
      const r = el.getBoundingClientRect();
      setTilt({
        x: ((e.clientX - r.left) / r.width - 0.5) * 2,
        y: ((e.clientY - r.top) / r.height - 0.5) * 2,
      });
    };
    const lv = () => setTilt({ x: 0, y: 0 });
    el.addEventListener("mousemove", mv);
    el.addEventListener("mouseleave", lv);
    return () => { el.removeEventListener("mousemove", mv); el.removeEventListener("mouseleave", lv); };
  }, []);

  const trendPath = useMemo(() => {
    const pts = candles.map((c, i) => ({ x: START_X + i * SPACING + W / 2, y: yFor(c.c) }));
    return pts.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(" ");
  }, [candles]);

  const areaPath = `${trendPath} L ${START_X + (candles.length - 1) * SPACING + W / 2} ${BOTTOM} L ${START_X + W / 2} ${BOTTOM} Z`;

  if (!mounted) return <div className="h-[400px] w-full animate-pulse bg-muted/20 rounded-xl" />;

  return (
    <div ref={wrapRef} className="relative select-none">
      {/* ── بَج toggle ── */}
      <div className="absolute right-2 top-2 z-20 flex items-center gap-1 rounded-full border border-violet-500/40 bg-background/70 p-1 backdrop-blur-md">
        {(Object.keys(SYMBOLS) as SymKey[]).map((k) => {
          const s = SYMBOLS[k];
          const active = k === sym;
          return (
            <button
              key={k}
              onClick={() => switchSym(k)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition ${
                active
                  ? "bg-violet-600 text-white shadow-[0_0_15px_rgba(139,92,246,0.5)]"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              type="button"
            >
              <IconOf kind={s.icon} className="h-3.5 w-3.5" />
              <span>{s.fa}</span>
            </button>
          );
        })}
      </div>

      {/* ── قیمت ── */}
      <div className="absolute left-2 top-2 z-20 flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <IconOf kind={conf.icon} className="h-4 w-4 text-violet-400" />
          <span className="text-xs font-medium text-muted-foreground">{conf.en}</span>
          <span className="text-[10px] text-muted-foreground/60">· {conf.faFull}</span>
        </div>
        <div key={price.k} className="price-pop font-mono text-2xl font-bold tabular-nums text-foreground">
          {Math.round(price.p).toLocaleString("fa-IR")}
        </div>
        <div className="flex items-center gap-1 text-xs font-medium">
          {price.up
            ? <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            : <TrendingDown className="h-3.5 w-3.5 text-rose-400" />}
          <span className={price.up ? "text-emerald-400" : "text-rose-400"}>
            {price.up ? "+" : "-"}{price.ch.toFixed(2)}%
          </span>
          <span className="text-muted-foreground">۲۴ ساعت</span>
        </div>
      </div>

      {/* ── چارت ── */}
      <div className="chart-wrap mt-24">
        <div
          className="chart-3d"
          style={{ transform: `rotateY(${-10 + tilt.x * 10}deg) rotateX(${4 - tilt.y * 8}deg) translateZ(0)` }}
        >
          <div className="relative">
            <div className="scan-bar" style={{ background: "linear-gradient(90deg, transparent, rgba(139,92,246,0.28), transparent)" }} />
            <svg viewBox="0 0 800 400" className={className} xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%"   stopColor="#8b5cf6" stopOpacity="0.15" />
                  <stop offset="50%"  stopColor="#a78bfa" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#c4b5fd" stopOpacity="1" />
                </linearGradient>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"   stopColor="#8b5cf6" stopOpacity="0.32" />
                  <stop offset="100%" stopColor="#6d28d9" stopOpacity="0" />
                </linearGradient>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="3" result="b" />
                  <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              </defs>

              {[...Array(6)].map((_, i) => (
                <line key={i} x1="0" y1={TOP + i * 46} x2="800" y2={TOP + i * 46}
                      stroke="currentColor" strokeOpacity="0.06" strokeWidth="1" />
              ))}

              <path d={areaPath} fill="url(#areaGrad)" />

              {candles.map((c, i) => {
                const x = START_X + i * SPACING;
                const green = c.c >= c.o;
                const col = green ? UP : DOWN;
                const yO = yFor(c.o), yC = yFor(c.c), yH = yFor(c.h), yL = yFor(c.l);
                const top = Math.min(yO, yC);
                const bodyH = Math.max(Math.abs(yC - yO), 5);
                const isLast = i === candles.length - 1;

                return (
                  <g key={c.id} className={isLast ? "pulse-glow" : undefined}>
                    <line x1={x + W / 2} y1={yH} x2={x + W / 2} y2={yL}
                          stroke={col.wick} strokeWidth="1.6" opacity="0.65" />
                    <path d={`M ${x} ${top} L ${x + W} ${top} L ${x + W + DX} ${top - DY} L ${x + DX} ${top - DY} Z`}
                          fill={col.top} className="candle-in" style={{ animationDelay: `${i * 0.04}s` }} />
                    <path d={`M ${x + W} ${top} L ${x + W + DX} ${top - DY} L ${x + W + DX} ${top + bodyH - DY} L ${x + W} ${top + bodyH} Z`}
                          fill={col.side} className="candle-in" style={{ animationDelay: `${i * 0.04}s` }} />
                    <rect x={x} y={top} width={W} height={bodyH} fill={col.front} rx="1.5"
                          className="candle-in" style={{ animationDelay: `${i * 0.04}s` }} />
                  </g>
                );
              })}

              <path d={trendPath} stroke="url(#lineGrad)" strokeWidth="2.5"
                    fill="none" strokeLinecap="round" strokeLinejoin="round"
                    filter="url(#glow)"
                    className="trend-line" />

              {candles.map((c, i) => {
                const x = START_X + i * SPACING;
                const green = c.c >= c.o;
                return (
                  <rect key={`v${c.id}`} x={x} y={385 - c.v} width={W} height={c.v}
                        fill={green ? "#10b981" : "#f43f5e"} opacity="0.32" rx="1.5"
                        className="candle-in" style={{ animationDelay: `${0.4 + i * 0.03}s` }} />
                );
              })}
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
