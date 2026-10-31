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
import { Badge } from "@/components/ui/badge";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { TiltCard } from "@/components/landing/tilt-card";

export const metadata = {
  title: "آموزش | SarvBots",
  description:
    "پلتفرم شفاف ارزیابی ربات‌های معاملاتی. ۱۰۰ هزار تومان رایگان برای مهمان، ۱۰ میلیون تومان با ثبت‌نام.",
};

const SECTIONS = [
  {
    id: "paper",
    icon: TrendingUp,
    step: "بخش ۱",
    title: "Paper Trading",
    subtitle: "بدون ریسک، با پول مجازی",
    description:
      "با سرمایه‌ی مجازی، استراتژی‌های معاملاتی را در محیطی شبیه‌سازی‌شده تمرین کن. بدون ریسک از دست دادن سرمایه‌ی واقعی.",
    cta: "شروع Paper Trading",
    href: "/paper-trading",
    features: [
      "سرمایه‌ی مجازی رایگان",
      "همان موتور اجرای Live",
      "بدون نیاز به کلید صرافی",
    ],
  },
  {
    id: "backtest",
    icon: BarChart3,
    step: "بخش ۲",
    title: "Backtest",
    subtitle: "استراتژی روی داده‌ی تاریخی",
    description:
      "عملکرد استراتژی‌ها را روی داده‌ی تاریخی BTC، ETH و SOL ببین. Profit Factor، Win Rate، و Max Drawdown — همه شفاف.",
    cta: "دیدن Backtest",
    href: "/backtest",
    features: [
      "داده‌ی ۵ ساله",
      "هزینه‌های واقعی (fee + slip)",
      "گزارش شفاف per-strategy",
    ],
  },
  {
    id: "paper-test",
    icon: BotIcon,
    step: "بخش ۳",
    title: "Paper Test",
    subtitle: "ربات‌های واقعی، در Paper Mode",
    description:
      "ربات‌های ما (Nooaah، SarvRouter) در Paper Mode ۲۴/۷ کار می‌کنند. عملکرد زنده‌شان را ببین، بدون هیچ تعهدی.",
    cta: "دیدن ربات‌ها",
    href: "/bots",
    features: [
      "وضعیت زنده (regime, gate)",
      "Backtest + Paper کنارِ هم",
      "آرشیو شفاف (۵ ربات غیرفعال)",
    ],
  },
  {
    id: "live",
    icon: Zap,
    step: "بخش ۴",
    title: "Live",
    subtitle: "بعد از ۳۰ روز Paper موفق",
    description:
      "هر ربات، قبل از Live، باید ۳۰ روز در Paper Mode موفق باشد. این محافظ، سرمایه‌ی تو را حفظ می‌کند.",
    cta: "ثبت‌نام برای Live",
    href: "/register",
    features: [
      "۳۰ روز Paper Mode الزامی",
      "Kill Switch فوری",
      "محدودیت‌های امنیتی سخت",
    ],
  },
] as const;

export default function LearnPage() {
  return (
    <div className="dark relative min-h-screen overflow-hidden bg-background text-foreground">
      <BackgroundFX />

      {/* HEADER — مثل landing */}
      <header className="relative z-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 pt-6">
          <Link href="/" className="flex items-center gap-2">
            <SarvLogo size={32} />
            <span className="text-sm font-semibold">SarvBots</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-violet-400"
          >
            بازگشت به خانه
            <ArrowLeft className="h-3 w-3" />
          </Link>
        </div>
      </header>

      {/* HERO */}
      <section className="relative z-10">
        <div className="mx-auto max-w-4xl px-6 pb-10 pt-12 text-center lg:pt-20">
          <Badge
            variant="outline"
            className="mb-6 border-violet-500/30 bg-violet-500/10 text-violet-200"
          >
            <Sparkles className="ml-1 h-3 w-3" />
            بدون نیاز به ثبت‌نام
          </Badge>

          <h1 className="mb-6 text-3xl font-bold leading-tight md:text-5xl lg:text-6xl">
            ۱۰۰ هزار تومان پول مجازی رایگان بگیرید.
            <br />
            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-violet-400 bg-clip-text text-transparent">
              با ثبت‌نام، ۹ میلیون و ۹۰۰ هزار تومان جایزه بگیرید.
            </span>
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-base text-muted-foreground md:text-lg">
            با این پول مجازی ترید کنید و بدون ریسک، ترید را یاد بگیرید.
            پلتفرم شفاف ارزیابی ربات‌های معاملاتی — Paper، Backtest، Paper Test و Live.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button
              asChild
              size="lg"
              className="border border-violet-400/50 bg-gradient-to-r from-violet-600 to-fuchsia-600 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_10px_40px_-10px_rgba(192,38,211,0.8)]"
            >
              <Link href="/guest" className="gap-2">
                شروع مهمان (۱۰۰k)
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="gap-2 border-violet-500/40">
              <Link href="/register">
                ثبت‌نام (۹.۹M)
                <CheckCircle2 className="h-4 w-4" />
              </Link>
            </Button>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-violet-400" /> بدون کارت بانکی
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3 text-violet-400" /> ۲ دقیقه راه‌اندازی
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-violet-400" /> Kill switch فوری
            </span>
          </div>
        </div>
      </section>

      {/* 4 sections — TiltCard + violet glass */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-16">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {SECTIONS.map((s) => {
            const Icon = s.icon;
            return (
              <TiltCard key={s.id}>
                <div className="group relative overflow-hidden rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-fuchsia-500/5 p-6 backdrop-blur-md transition-all duration-300 hover:border-violet-400/50 hover:shadow-[0_20px_60px_-20px_rgba(139,92,246,0.4)]">
                  {/* subtle glow */}
                  <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-violet-500/20 blur-2xl" />

                  <div className="relative mb-4 flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-violet-500/30 bg-violet-500/10 text-violet-300">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-[10px] text-violet-300/70">
                        {s.step} <span className="mx-1">·</span> {s.subtitle}
                      </p>
                      <h2 className="text-lg font-semibold">{s.title}</h2>
                    </div>
                  </div>

                  <p className="relative mb-4 text-sm leading-relaxed text-muted-foreground">
                    {s.description}
                  </p>

                  <ul className="relative mb-5 space-y-1.5 text-sm">
                    {s.features.map((f) => (
                      <li key={f} className="flex items-start gap-2">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    asChild
                    variant="outline"
                    className="relative w-full gap-2 border-violet-500/30 hover:bg-violet-500/10 hover:text-violet-200"
                  >
                    <Link href={s.href}>
                      {s.cta}
                      <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
                    </Link>
                  </Button>
                </div>
              </TiltCard>
            );
          })}
        </div>
      </section>

      {/* Footer CTA */}
      <section className="relative z-10 border-t border-violet-500/20 bg-black/40 backdrop-blur-md">
        <div className="mx-auto max-w-4xl px-6 py-14 text-center">
          <h2 className="mb-3 text-2xl font-bold md:text-3xl">آماده‌ای شروع کنی؟</h2>
          <p className="mx-auto mb-8 max-w-xl text-sm text-muted-foreground">
            با ۱۰۰ هزار تومان پول مجازی رایگان شروع کن. هر وقت آماده بودی، ثبت‌نام کن و ۹.۹ میلیون تومان جایزه بگیر.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button
              asChild
              size="lg"
              className="border border-violet-400/50 bg-gradient-to-r from-violet-600 to-fuchsia-600 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_10px_40px_-10px_rgba(192,38,211,0.8)]"
            >
              <Link href="/guest" className="gap-2">
                شروع مهمان (۱۰۰k)
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="border-violet-500/40">
              <Link href="/register">ثبت‌نام (۹.۹M)</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
