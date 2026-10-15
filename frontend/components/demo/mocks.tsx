/**
 * Mock previews برای صفحه‌ی دمو.
 * هر کامپوننت، یک نمایش کوچک از یک قابلیت پلتفرمه.
 * داده‌ها mock ان — تم بنفش/دارک.
 */

/* ───── ۱. سیگنال‌ها ───── */
export function SignalsMock() {
  const items = [
    { sym: "BTCTMN",  dir: "خرید", conf: 88, ch: +2.4 },
    { sym: "ETHTMN",  dir: "فروش", conf: 72, ch: -1.8 },
    { sym: "SOLTMN",  dir: "خرید", conf: 81, ch: +3.1 },
  ];
  return (
    <div className="space-y-2">
      {items.map((s) => {
        const buy = s.dir === "خرید";
        return (
          <div
            key={s.sym}
            className="flex items-center justify-between rounded-lg border border-violet-500/15 bg-background/50 px-3 py-2"
          >
            <div className="flex items-center gap-3">
              <span
                className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                  buy
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "bg-rose-500/15 text-rose-400"
                }`}
              >
                {s.dir}
              </span>
              <span className="font-mono text-xs font-semibold">{s.sym}</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <div className="h-1 w-12 rounded-full bg-violet-500/20">
                  <div
                    className="h-full rounded-full bg-violet-400"
                    style={{ width: `${s.conf}%` }}
                  />
                </div>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {s.conf}%
                </span>
              </div>
              <span
                className={`font-mono text-xs font-semibold ${
                  s.ch >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {s.ch >= 0 ? "+" : ""}
                {s.ch}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ───── ۲. شخصیت ارز ───── */
export function CoinPersonalityMock() {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm font-bold">BTCTMN</span>
        <span className="rounded bg-rose-500/15 px-2 py-0.5 text-[10px] text-rose-300">
          روند نزولی
        </span>
      </div>
      <svg viewBox="0 0 240 60" className="w-full">
        <defs>
          <linearGradient id="mock-personality" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fb7185" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#fb7185" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d="M 0 10 Q 40 18, 70 22 T 130 35 T 190 45 T 240 55 L 240 60 L 0 60 Z"
          fill="url(#mock-personality)"
        />
        <path
          d="M 0 10 Q 40 18, 70 22 T 130 35 T 190 45 T 240 55"
          stroke="#fb7185"
          strokeWidth="2"
          fill="none"
        />
      </svg>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
          <p className="font-mono text-sm font-bold text-violet-300">۷۸</p>
          <p className="text-[9px] text-muted-foreground">قدرت روند</p>
        </div>
        <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
          <p className="font-mono text-sm font-bold text-violet-300">متوسط</p>
          <p className="text-[9px] text-muted-foreground">نوسان</p>
        </div>
        <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
          <p className="font-mono text-sm font-bold text-violet-300">بالا</p>
          <p className="text-[9px] text-muted-foreground">حجم</p>
        </div>
      </div>
    </div>
  );
}

/* ───── ۳. اسکنر بازار ───── */
export function ScannerMock() {
  const rows = [
    { sym: "SOLTMN",  score: 92, ch: +4.2 },
    { sym: "BTCTMN",  score: 85, ch: +2.4 },
    { sym: "PEPETMN", score: 71, ch: +8.9 },
    { sym: "ETHTMN",  score: 64, ch: -1.8 },
  ];
  return (
    <div className="space-y-1.5">
      <div className="grid grid-cols-[1fr_auto_auto] gap-2 px-3 pb-1 text-[9px] uppercase tracking-wider text-muted-foreground/60">
        <span>نماد</span>
        <span>امتیاز</span>
        <span>تغییر</span>
      </div>
      {rows.map((r) => (
        <div
          key={r.sym}
          className="grid grid-cols-[1fr_auto_auto] items-center gap-2 rounded-lg border border-violet-500/15 bg-background/50 px-3 py-2"
        >
          <span className="font-mono text-xs font-semibold">{r.sym}</span>
          <div className="flex items-center gap-1.5">
            <div className="h-1 w-10 rounded-full bg-violet-500/20">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500"
                style={{ width: `${r.score}%` }}
              />
            </div>
            <span className="font-mono text-[10px] text-violet-300">
              {r.score}
            </span>
          </div>
          <span
            className={`font-mono text-xs font-semibold ${
              r.ch >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {r.ch >= 0 ? "+" : ""}
            {r.ch}%
          </span>
        </div>
      ))}
    </div>
  );
}

/* ───── ۴. بک‌تست ───── */
export function BacktestMock() {
  return (
    <div className="space-y-3">
      <svg viewBox="0 0 240 70" className="w-full">
        <defs>
          <linearGradient id="mock-equity" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d="M 0 55 L 30 45 L 55 52 L 85 35 L 115 42 L 145 25 L 175 38 L 205 22 L 240 8 L 240 70 L 0 70 Z"
          fill="url(#mock-equity)"
        />
        <path
          d="M 0 55 L 30 45 L 55 52 L 85 35 L 115 42 L 145 25 L 175 38 L 205 22 L 240 8"
          stroke="#10b981"
          strokeWidth="2"
          fill="none"
          strokeLinejoin="round"
        />
      </svg>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/5 py-2">
          <p className="font-mono text-sm font-bold text-emerald-400">۶۸٪</p>
          <p className="text-[9px] text-muted-foreground">Win Rate</p>
        </div>
        <div className="rounded-lg border border-violet-500/15 bg-background/40 py-2">
          <p className="font-mono text-sm font-bold text-violet-300">۲.۱</p>
          <p className="text-[9px] text-muted-foreground">Sharpe</p>
        </div>
        <div className="rounded-lg border border-rose-500/15 bg-rose-500/5 py-2">
          <p className="font-mono text-sm font-bold text-rose-400">-۸٪</p>
          <p className="text-[9px] text-muted-foreground">Max DD</p>
        </div>
      </div>
    </div>
  );
}

/* ───── ۵. ربات‌ها ───── */
export function BotsMock() {
  const bots = ["نوح", "گرید", "دنبال‌کننده", "اسکالپ", "شکارچی", "پورتفو"];
  return (
    <div className="grid grid-cols-2 gap-2">
      {bots.map((b) => (
        <div
          key={b}
          className="flex items-center gap-2 rounded-lg border border-violet-500/15 bg-background/50 px-3 py-2.5"
        >
          <div className="h-6 w-6 rounded-md bg-gradient-to-br from-violet-500/40 to-emerald-500/10" />
          <span className="text-xs font-medium">{b}</span>
        </div>
      ))}
    </div>
  );
}

/* ───── ۶. کیف پول ربات ───── */
export function WalletMock() {
  const donut = [
    { label: "نوح",   pct: 45, color: "#a78bfa" },
    { label: "گرید",  pct: 25, color: "#8b5cf6" },
    { label: "اسکالپ",pct: 18, color: "#c084fc" },
    { label: "سایر",  pct: 12, color: "#6d28d9" },
  ];
  let offset = 0;
  const R = 30;
  const C = 2 * Math.PI * R;
  return (
    <div className="flex items-center gap-4">
      <svg viewBox="0 0 80 80" className="h-20 w-20 shrink-0">
        <circle cx="40" cy="40" r={R} fill="none" stroke="rgba(139,92,246,0.1)" strokeWidth="12" />
        {donut.map((d, i) => {
          const dash = (d.pct / 100) * C;
          const el = (
            <circle
              key={i}
              cx="40"
              cy="40"
              r={R}
              fill="none"
              stroke={d.color}
              strokeWidth="12"
              strokeDasharray={`${dash} ${C - dash}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 40 40)"
            />
          );
          offset += dash;
          return el;
        })}
      </svg>
      <div className="flex-1 space-y-1">
        {donut.map((d) => (
          <div key={d.label} className="flex items-center gap-2 text-[11px]">
            <span className="h-2 w-2 rounded-full" style={{ background: d.color }} />
            <span className="flex-1 text-muted-foreground">{d.label}</span>
            <span className="font-mono text-foreground/90">{d.pct}٪</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ───── ۷. سفارشات ───── */
export function OrdersMock() {
  const orders = [
    { sym: "BTCTMN",  side: "خرید", status: "پر",   color: "emerald" },
    { sym: "ETHTMN",  side: "فروش", status: "باز",  color: "violet" },
    { sym: "SOLTMN",  side: "خرید", status: "لغو",  color: "rose" },
  ];
  const colorMap: Record<string, string> = {
    emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    violet:  "border-violet-500/30 bg-violet-500/10 text-violet-300",
    rose:    "border-rose-500/30 bg-rose-500/10 text-rose-400",
  };
  return (
    <div className="space-y-2">
      {orders.map((o) => (
        <div
          key={o.sym}
          className="flex items-center justify-between rounded-lg border border-violet-500/15 bg-background/50 px-3 py-2"
        >
          <span className="font-mono text-xs font-semibold">{o.sym}</span>
          <span className="text-[11px] text-muted-foreground">{o.side}</span>
          <span className={`rounded border px-2 py-0.5 text-[10px] ${colorMap[o.color]}`}>
            {o.status}
          </span>
        </div>
      ))}
    </div>
  );
}
