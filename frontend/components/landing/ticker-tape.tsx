"use client";

const SYMBOLS = [
  { s: "BTCTMN", p: 21_500_000_000, ch: +1.24 },
  { s: "ETHTMN", p: 3_210_000_000, ch: -0.58 },
  { s: "USDTTMN", p: 8_950_000, ch: +0.12 },
  { s: "XRPTMN", p: 245_000, ch: +2.31 },
  { s: "DOGETMN", p: 18_400, ch: -1.05 },
  { s: "SOLTMN", p: 1_820_000, ch: +3.42 },
  { s: "ADATMN", p: 62_300, ch: -0.21 },
  { s: "BNBTMN", p: 13_200_000, ch: +0.87 },
  { s: "TRXTMN", p: 28_700, ch: +1.11 },
  { s: "DASHTMN", p: 950_000, ch: -0.34 },
];

const fmt = (n: number) =>
  n > 1_000_000_000
    ? `${(n / 1_000_000_000).toFixed(2)}B`
    : n > 1_000_000
      ? `${(n / 1_000_000).toFixed(2)}M`
      : n.toLocaleString("en-US");

export function TickerTape() {
  const items = [...SYMBOLS, ...SYMBOLS];
  return (
    <div className="relative overflow-hidden border-y border-violet-500/15 bg-background/60 backdrop-blur-sm">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-20 bg-gradient-to-r from-background to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-20 bg-gradient-to-l from-background to-transparent" />
      <div className="ticker-track py-2.5">
        {items.map((it, i) => {
          const up = it.ch >= 0;
          return (
            <div key={i} className="mx-6 inline-flex items-center gap-2 font-mono text-xs">
              <span className="font-bold text-foreground/90">{it.s}</span>
              <span className="text-muted-foreground">{fmt(it.p)}</span>
              <span className={up ? "text-violet-400" : "text-fuchsia-400"}>
                {up ? "▲" : "▼"} {Math.abs(it.ch).toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
