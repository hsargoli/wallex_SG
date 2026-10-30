import Link from "next/link";
import {
  Sparkles,
  TrendingUp,
  BarChart3,
  Bot as BotIcon,
  Zap,
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const metadata = {
  title: "آموزش | SarvBots",
  description:
    "پلتفرم شفاف ارزیابی ربات‌های معاملاتی. ۱۰۰ هزار تومان رایگان برای مهمان، ۱۰ میلیون تومان با ثبت‌نام.",
};

const SECTIONS = [
  {
    id: "paper",
    icon: TrendingUp,
    title: "Paper Trading",
    subtitle: "بدون ریسک، با پول مجازی",
    description:
      "با سرمایه‌ی مجازی، استراتژی‌های معاملاتی را در محیطی شبیه‌سازی‌شده تمرین کن. بدون ریسک از دست دادن سرمایه‌ی واقعی.",
    cta: "شروع Paper Trading",
    href: "/paper-trading",
    tone: "emerald",
    features: [
      "سرمایه‌ی مجازی رایگان",
      "همان موتور اجرای Live",
      "بدون نیاز به کلید صرافی",
    ],
  },
  {
    id: "backtest",
    icon: BarChart3,
    title: "Backtest",
    subtitle: "استراتژی روی داده‌ی تاریخی",
    description:
      "عملکرد استراتژی‌ها را روی داده‌ی تاریخی BTC، ETH و SOL ببین. Profit Factor، Win Rate، و Max Drawdown — همه شفاف.",
    cta: "دیدن Backtest",
    href: "/backtest",
    tone: "violet",
    features: [
      "داده‌ی ۵ ساله",
      "هزینه‌های واقعی (fee + slip)",
      "گزارش شفاف per-strategy",
    ],
  },
  {
    id: "paper-test",
    icon: BotIcon,
    title: "Paper Test",
    subtitle: "ربات‌های واقعی، در Paper Mode",
    description:
      "ربات‌های ما (Nooaah، SarvRouter) در Paper Mode ۲۴/۷ کار می‌کنند. عملکرد زنده‌شان را ببین، بدون هیچ تعهدی.",
    cta: "دیدن ربات‌ها",
    href: "/bots",
    tone: "sky",
    features: [
      "وضعیت زنده (regime, gate)",
      "Backtest + Paper کنارِ هم",
      "آرشیو شفاف (۵ ربات غیرفعال)",
    ],
  },
  {
    id: "live",
    icon: Zap,
    title: "Live",
    subtitle: "بعد از ۳۰ روز Paper موفق",
    description:
      "هر ربات، قبل از Live، باید ۳۰ روز در Paper Mode موفق باشد. این محافظ، سرمایه‌ی تو را حفظ می‌کند.",
    cta: "ثبت‌نام برای Live",
    href: "/register",
    tone: "amber",
    features: [
      "۳۰ روز Paper Mode الزامی",
      "Kill Switch فوری",
      "محدودیت‌های امنیتی سخت",
    ],
  },
] as const;

const TONES: Record<string, string> = {
  emerald: "border-emerald-500/30 bg-emerald-500/5",
  violet: "border-violet-500/30 bg-violet-500/5",
  sky: "border-sky-500/30 bg-sky-500/5",
  amber: "border-amber-500/30 bg-amber-500/5",
};

const ICON_TONES: Record<string, string> = {
  emerald: "text-emerald-400",
  violet: "text-violet-400",
  sky: "text-sky-400",
  amber: "text-amber-400",
};

export default function LearnPage() {
  return (
    <div dir="rtl" className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/40">
        <div className="container mx-auto flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            <span className="text-sm text-muted-foreground">بازگشت به خانه</span>
          </Link>
          <div className="text-sm font-semibold">SarvBots</div>
        </div>
      </header>

      {/* Hero */}
      <section className="container mx-auto px-4 py-14 md:py-20 text-center">
        <Badge variant="outline" className="mb-5">
          <Sparkles className="h-3 w-3 ml-1" /> بدون نیاز به ثبت‌نام
        </Badge>
        <h1 className="text-3xl md:text-5xl font-bold mb-5 leading-tight">
          ۱۰۰ هزار تومان رایگان.
          <br />
          <span className="text-emerald-400">با ثبت‌نام، ۱۰ میلیون تومان.</span>
        </h1>
        <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
          پلتفرم شفاف ارزیابی ربات‌های معاملاتی. Paper، Backtest، Paper Test، و
          Live — همه در یک جا، بدون بدهی پنهان.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link href="/guest">
            <Button size="lg" className="gap-2">
              شروع مهمان (۱۰۰k)
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/register">
            <Button size="lg" variant="outline" className="gap-2">
              ثبت‌نام (۱۰M)
              <CheckCircle2 className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-6 mt-10 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <ShieldCheck className="h-3 w-3" /> بدون کارت بانکی
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" /> ۲ دقیقه راه‌اندازی
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" /> Kill switch فوری
          </span>
        </div>
      </section>

      {/* 4 sections */}
      <section className="container mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {SECTIONS.map((s, i) => {
            const Icon = s.icon;
            return (
              <Card key={s.id} className={TONES[s.tone]}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div
                      className={`rounded-lg bg-background/50 p-2 ${ICON_TONES[s.tone]}`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          بخش {i + 1}
                        </span>
                        <Badge variant="outline" className="text-[10px]">
                          {s.subtitle}
                        </Badge>
                      </div>
                      <CardTitle className="text-lg mt-1">{s.title}</CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {s.description}
                  </p>
                  <ul className="space-y-1.5 text-sm">
                    {s.features.map((f) => (
                      <li key={f} className="flex items-start gap-2">
                        <CheckCircle2
                          className={`h-4 w-4 mt-0.5 shrink-0 ${ICON_TONES[s.tone]}`}
                        />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href={s.href}>
                    <Button variant="outline" className="w-full mt-2 gap-2">
                      {s.cta}
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Footer CTA */}
      <section className="border-t border-border/40">
        <div className="container mx-auto px-4 py-12 text-center">
          <h2 className="text-2xl font-bold mb-3">آماده‌ای شروع کنی؟</h2>
          <p className="text-sm text-muted-foreground mb-6 max-w-xl mx-auto">
            با ۱۰۰ هزار تومان رایگان شروع کن. هر وقت آماده بودی، ثبت‌نام کن و
            ۱۰ میلیون تومان بگیر.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link href="/guest">
              <Button size="lg" className="gap-2">
                شروع مهمان (۱۰۰k)
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/register">
              <Button size="lg" variant="outline">
                ثبت‌نام (۱۰M)
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
