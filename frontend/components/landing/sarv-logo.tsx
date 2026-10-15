/**
 * SarvLogo — درخت سرو (نماد SarvBots) — سبز.
 * تنها المان سبز در کل لندینگ.
 */
export function SarvLogo({ size = 36 }: { size?: number }) {
  return (
    <svg
      viewBox="0 0 100 130"
      width={size}
      height={size * 1.3}
      xmlns="http://www.w3.org/2000/svg"
      aria-label="SarvBots"
    >
      <defs>
        <linearGradient id="sarvGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#34d399" />
          <stop offset="50%" stopColor="#10b981" />
          <stop offset="100%" stopColor="#047857" />
        </linearGradient>
        <filter id="sarvGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.6" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* تنه */}
      <rect x="47" y="98" width="6" height="26" rx="2" fill="#5b3a1c" />
      <rect x="47" y="98" width="2" height="26" fill="#7a5128" opacity="0.6" />

      {/* برگ‌ها — لایه‌به‌لایه (شکل سرو ایرانی) */}
      <g filter="url(#sarvGlow)">
        <path d="M50 4 L60 30 L40 30 Z" fill="url(#sarvGrad)" />
        <path d="M50 18 L64 46 L36 46 Z" fill="url(#sarvGrad)" />
        <path d="M50 34 L68 64 L32 64 Z" fill="url(#sarvGrad)" />
        <path d="M50 52 L72 84 L28 84 Z" fill="url(#sarvGrad)" />
        <path d="M50 72 L76 102 L24 102 Z" fill="url(#sarvGrad)" />
      </g>

      {/* هایلایت */}
      <path d="M50 4 L56 28 L50 28 Z" fill="#a7f3d0" opacity="0.55" />
      <path d="M50 18 L58 44 L50 44 Z" fill="#a7f3d0" opacity="0.4" />
    </svg>
  );
}
