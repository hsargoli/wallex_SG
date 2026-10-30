"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bot, ArrowLeft, Zap, Activity, Cpu, FlaskConical, Play } from "lucide-react";
import { useBots } from "@/lib/queries";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { SUPPORT, NON_TRADING } from "@/lib/bot-support";


const TAGS_FA: Record<string, string> = {
  passive: "منفعل",
  range_trading: "معامله در محدوده",
  grid: "شبکه‌ای",
  ema_cross: "تقاطع EMA",
  momentum: "مومنتوم",
  trend_following: "دنبال‌کردن روند",
  bottom_hunting: "شکار کف",
  scalping: "اسکالپ",
  mean_reversion: "بازگشت به میانگین",
  regime_based: "بر پایه‌ی رژیم بازار",
  portfolio: "پورتفو",
  meta: "فرا‌ربات",
  volatility: "نوسان",
  monitor: "پایش",
  scanner: "اسکنر",
  dip_buy: "خرید افت",
};

const EXTRA_CAPS_FA: Record<string, string> = {
  monitor: "پایش",
  signal: "سیگنال",
  scan: "اسکن",
  display: "نمایش",
};

type BotItem = {
  slug: string;
  name: string;
  name_en: string;
  version: string;
  description: string;
  tags: string[];
  capabilities: string[];
  archived?: boolean;
};

const score = (slug: string) =>
  (SUPPORT[slug]?.paper ? 2 : 0) + (SUPPORT[slug]?.backtest ? 1 : 0);

export default function BotsListPage() {
  const bots = useBots();
  const list: BotItem[] = [...(bots.data?.bots ?? [])].sort(
    (a, b) => score(b.slug) - score(a.slug),
  );
  const nBacktest = list.filter((b) => SUPPORT[b.slug]?.backtest).length;
  const nPaper = list.filter((b) => SUPPORT[b.slug]?.paper).length;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Bot className="h-6 w-6 text-emerald-400" />
            ربات‌های معاملاتی
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {bots.data
              ? `${bots.data.count} ربات · ${nBacktest} قابل بک‌تست · ${nPaper} قابل تست زنده`
              : "در حال بارگذاری..."}
          </p>
          <p className="mt-1 text-xs text-muted-foreground/80">
            مسیر پیشنهادی: اول بک‌تست روی داده‌ی گذشته، بعد تست زنده بدون پول واقعی.
          </p>
        </div>
      </div>

      {bots.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      ) : list.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Bot className="mx-auto mb-3 h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">هنوز رباتی ثبت نشده</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {list.map((bot) => (
            <BotCard key={bot.slug} bot={bot} />
          ))}
        </div>
      )}
    </div>
  );
}

function StageChip({
  icon: Icon,
  label,
  on,
  href,
}: {
  icon: React.ElementType;
  label: string;
  on: boolean;
  href?: string;
}) {
  const router = useRouter();
  const act = (e: React.SyntheticEvent) => {
    if (!on || !href) return; // چیپ غیرفعال: اجازه بده کلیک به صفحه‌ی جزئیات برود
    e.preventDefault();
    e.stopPropagation();
    router.push(href);
  };
  return (
    <span
      role={on ? "button" : undefined}
      tabIndex={on ? 0 : undefined}
      onClick={act}
      onKeyDown={(e) => {
        if (e.key === "Enter") act(e);
      }}
      title={on ? undefined : "هنوز برای این ربات آماده نیست"}
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[10px] transition",
        on
          ? "cursor-pointer border-emerald-500/30 bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 dark:text-emerald-400"
          : "border-zinc-500/20 bg-zinc-500/5 text-muted-foreground/60",
      )}
    >
      <Icon className="h-3 w-3" />
      {label}
      {!on && <span className="opacity-70">· به‌زودی</span>}
    </span>
  );
}

function BotCard({ bot }: { bot: BotItem }) {
  const sup = SUPPORT[bot.slug] ?? { backtest: false, paper: false };
  const trading = !NON_TRADING.has(bot.slug);
  const extras = bot.capabilities.filter((c) => !["paper", "live", "backtest"].includes(c));

  return (
    <Link href={`/bots/${bot.slug}`} className="group block">
      <Card className="h-full transition hover:border-emerald-500/40 hover:bg-emerald-500/5">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/30 to-emerald-500/0">
                <Bot className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-base">{bot.name}</CardTitle>
                <CardDescription className="text-xs">{bot.name_en}</CardDescription>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1">
              <Badge variant="outline" className="text-[10px]">
                v{bot.version}
              </Badge>
              {bot.archived ? (
                <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-[10px] text-amber-400">
                  آرشیو
                </Badge>
              ) : (
                <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[10px] text-emerald-400">
                  فعال (Paper)
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="line-clamp-2 text-sm text-muted-foreground">{bot.description}</p>

          {bot.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {bot.tags.slice(0, 3).map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="border-blue-500/20 bg-blue-500/5 text-[10px] text-blue-500 dark:text-blue-400"
                >
                  {TAGS_FA[tag] ?? tag}
                </Badge>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between border-t border-white/5 pt-3">
            <div className="flex flex-wrap gap-1.5">
              {trading && (
                <>
                  <StageChip
                    icon={FlaskConical}
                    label="بک‌تست"
                    on={sup.backtest}
                    href={`/backtest?bot=${bot.slug}`}
                  />
                  <StageChip icon={Play} label="تست زنده" on={sup.paper} href="/paper-trading" />
                </>
              )}
              {extras.map((c) => (
                <Badge
                  key={c}
                  variant="outline"
                  className="gap-1 border-zinc-500/30 text-[9px] text-muted-foreground"
                >
                  {c === "signal" ? <Zap className="h-2.5 w-2.5" /> : c === "monitor" ? <Activity className="h-2.5 w-2.5" /> : <Cpu className="h-2.5 w-2.5" />}
                  {EXTRA_CAPS_FA[c] ?? c}
                </Badge>
              ))}
            </div>
            <ArrowLeft className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:-translate-x-1 group-hover:text-emerald-400" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
