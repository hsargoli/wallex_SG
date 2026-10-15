/**
 * CandlestickSVG — چارت کندل استیک با خط روند، سایه، و حجم.
 * طراحی برای لندینگ SarvBots — سبز درخشان، حس رشد.
 */

const CANDLES = [
  { o: 100, c: 105, h: 108, l: 98 },
  { o: 105, c: 103, h: 107, l: 101 },
  { o: 103, c: 110, h: 112, l: 102 },
  { o: 110, c: 115, h: 118, l: 108 },
  { o: 115, c: 113, h: 117, l: 111 },
  { o: 113, c: 118, h: 120, l: 112 },
  { o: 118, c: 122, h: 125, l: 116 },
  { o: 122, c: 120, h: 124, l: 118 },
  { o: 120, c: 128, h: 130, l: 119 },
  { o: 128, c: 135, h: 138, l: 126 },
  { o: 135, c: 133, h: 137, l: 131 },
  { o: 133, c: 142, h: 145, l: 132 },
  { o: 142, c: 150, h: 153, l: 140 },
  { o: 150, c: 148, h: 152, l: 146 },
  { o: 148, c: 158, h: 162, l: 147 },
];

const VOLUMES = [18, 28, 20, 35, 22, 40, 28, 24, 45, 38, 26, 42, 50, 30, 55];

const MIN_P = 90;
const MAX_P = 165;
const CHART_TOP = 40;
const CHART_BOTTOM = 340;
const CHART_HEIGHT = CHART_BOTTOM - CHART_TOP;

const yFor = (p: number) =>
  CHART_BOTTOM - ((p - MIN_P) / (MAX_P - MIN_P)) * CHART_HEIGHT;

const SPACING = 48;
const START_X = 30;
const BODY_W = 24;

export function CandlestickSVG({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 800 420"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="چارت کندل استیک"
    >
      <defs>
        <linearGradient id="trendLineGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.1" />
          <stop offset="50%" stopColor="#10b981" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#34d399" stopOpacity="1" />
        </linearGradient>
        <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
        </linearGradient>
        <filter id="glowFilter">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Grid (افقی) */}
      {[...Array(7)].map((_, i) => (
        <line
          key={`h${i}`}
          x1="0"
          y1={CHART_TOP + i * 50}
          x2="800"
          y2={CHART_TOP + i * 50}
          stroke="currentColor"
          strokeOpacity="0.05"
          strokeWidth="1"
        />
      ))}

      {/* Area زیر خط روند */}
      <path
        d="M 30 340 Q 250 280, 450 200 T 770 60 L 770 340 Z"
        fill="url(#areaFill)"
      />

      {/* کندل‌ها */}
      {CANDLES.map((c, i) => {
        const x = START_X + i * SPACING;
        const isGreen = c.c >= c.o;
        const yO = yFor(c.o);
        const yC = yFor(c.c);
        const yH = yFor(c.h);
        const yL = yFor(c.l);
        const bodyTop = Math.min(yO, yC);
        const bodyHeight = Math.max(Math.abs(yC - yO), 4);
        const color = isGreen ? "#10b981" : "#ef4444";
        const darkColor = isGreen ? "#047857" : "#b91c1c";

        return (
          <g key={i}>
            {/* Wick */}
            <line
              x1={x + BODY_W / 2}
              y1={yH}
              x2={x + BODY_W / 2}
              y2={yL}
              stroke={color}
              strokeWidth="1.5"
              opacity="0.6"
            />
            {/* 3D edge (سمت راست) */}
            <rect
              x={x + BODY_W}
              y={bodyTop + 3}
              width="4"
              height={bodyHeight - 3}
              fill={darkColor}
              opacity="0.7"
            />
            {/* Body */}
            <rect
              x={x}
              y={bodyTop}
              width={BODY_W}
              height={bodyHeight}
              fill={color}
              rx="1"
            />
          </g>
        );
      })}

      {/* خط روند */}
      <path
        d="M 30 320 Q 250 260, 450 180 T 760 70"
        stroke="url(#trendLineGrad)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
        filter="url(#glowFilter)"
      />

      {/* حجم */}
      {VOLUMES.map((v, i) => {
        const x = START_X + i * SPACING;
        const isGreen = CANDLES[i].c >= CANDLES[i].o;
        return (
          <rect
            key={`v${i}`}
            x={x}
            y={400 - v}
            width={BODY_W}
            height={v}
            fill={isGreen ? "#10b981" : "#ef4444"}
            opacity="0.3"
            rx="1"
          />
        );
      })}
    </svg>
  );
}
