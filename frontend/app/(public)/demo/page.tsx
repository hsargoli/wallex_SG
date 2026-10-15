import Link from "next/link";
import {
  ArrowRight, ArrowLeft, Zap, Brain, Radar, FlaskConical,
  Bot, Wallet, ClipboardList, Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import {
  SignalsMock, CoinPersonalityMock, ScannerMock, BacktestMock,
  BotsMock, WalletMock, OrdersMock,
} from "@/components/demo/mocks";

const SECTIONS = [
  {
    icon: Zap,
    title: "سیگنال‌های خرید و فروش",
    desc: "نقاط ورود و خروج با تأییدیه‌ی چندلایه — قدرت، اعتماد، و جهت.",
    href: "/signals",
    preview: <SignalsMock />,
  },
  {
    icon: Brain,
    title: "شخصیت ارز",
    desc: "رژیم بازار، قدرت روند، نوسان، و رفتار هر نماد در یک نگاه.",
    href: "/analysis",
    preview: <CoinPersonalityMock />,
  },
  {
    icon: Radar,
    title: "اسکنر بازار",
    desc: "بین صدها نماد، بهترین فرصت‌ها را در چند ثانیه پیدا کن.",
    href: "/scanner",
    preview: <ScannerMock />,
  },
  {
    icon: FlaskConical,
    title: "بک‌تست",
    desc: "قبل از معامله‌ی واقعی، استراتژی را روی داده‌ی گذشته بسنج.",
    href: "/backtest",
    preview: <BacktestMock />,
  },
  {
    icon: Bot,
    title: "ربات‌های معاملاتی",
    desc: "استراتژی‌های متنوع برای شرایط مختلف بازار، آماده‌ی اجرا.",
    href: "/bots",
    preview: <BotsMock />,
  },
  {
    icon: Wallet,
    title: "کیف پول ربات",
    desc: "توزیع بودجه بین ربات‌ها، سودآوری هر کدام، و مدیریت ریسک.",
    href: "/bot-wallet",
    preview: <WalletMock />,
  },
  {
    icon: ClipboardList,
    title: "سفارش‌ها",
    desc: "تاریخچه‌ی کامل سفارش‌ها — باز، پر شده، یا لغو شده.",
    href: "/orders",
    preview: <OrdersMock />,
  },
];

export default function DemoPage() {
  return (
    <div className="dark relative min-h-screen overflow-hidden bg-background text-foreground">
      <BackgroundFX />

      {/* ── Header ── */}
      <header className="relative z-10 border-b border-violet-500/15">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <Link href="/" className="flex items-center gap-3 transition hover:opacity-80">
            <SarvLogo size={32} />
            <div>
              <p className="text-sm font-semibold">SarvBots</p>
              <p className="text-[10px] text-muted-foreground">رشد پایدار سبز</p>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-2 border-violet-500/40 bg-violet-600/10 text-violet-300">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
              نمایشگاه قابلیت‌ها
            </Badge>
            <Button asChild size="sm" variant="outline" className="gap-2 border-violet-500/40 hover:bg-violet-600/10">
              <Link href="/">
                <ArrowRight className="h-3.5 w-3.5" />
                بازگشت
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative z-10">
        <div className="mx-auto max-w-4xl px-6 pb-4 pt-14 text-center">
          <Badge variant="outline" className="mb-5 gap-2 border-violet-500/40 bg-violet-600/10 text-violet-300">
            <Sparkles className="h-3 w-3" />
            نمایشگاه زنده
          </Badge>
          <h1 className="text-3xl font-bold tracking-tight lg:text-5xl">
            <span className="bg-gradient-to-l from-violet-200 via-violet-400 to-purple-600 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(139,92,246,0.5)]">
              چه کارهایی می‌تونی انجام بدی
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-muted-foreground lg:text-base">
            یه گشت سریع توی پلتفرم. هر کارت، یه قابلیت — روی هر کدام کلیک کنی،
            به بخش واقعی‌اش توی داشبورد می‌ری.
          </p>
        </div>
      </section>

      {/* ── Sections ── */}
      <section className="relative z-10">
        <div className="mx-auto max-w-7xl px-6 py-12">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {SECTIONS.map((s, i) => {
              const Icon = s.icon;
              const wide = i === 0 || i === 6; // سیگنال‌ها و سفارشات: کارت پهن‌تر
              return (
                <Link
                  key={s.title}
                  href={s.href}
                  className={`group block ${wide ? "lg:col-span-2" : ""}`}
                >
                  <Card className="relative h-full overflow-hidden border-violet-500/15 bg-background/60 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-violet-500/50 hover:bg-violet-600/[0.07] hover:shadow-[0_0_40px_-10px_rgba(139,92,246,0.45)]">
                    {/* نوار رنگی بالا */}
                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

                    <CardContent className="flex h-full flex-col gap-4 p-6">
                      {/* Header */}
                      <div className="flex items-start gap-3">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/40 to-fuchsia-600/10 ring-1 ring-violet-500/20">
                          <Icon className="h-5 w-5 text-violet-300" />
                        </div>
                        <div className="flex-1 pt-0.5">
                          <h3 className="text-sm font-semibold leading-tight">
                            {s.title}
                          </h3>
                          <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                            {s.desc}
                          </p>
                        </div>
                      </div>

                      {/* Preview */}
                      <div className="mt-auto rounded-xl border border-violet-500/10 bg-violet-500/[0.03] p-3">
                        {s.preview}
                      </div>

                      {/* Footer hint */}
                      <div className="flex items-center justify-between pt-1 text-[10px] text-muted-foreground/70">
                        <span className="transition-colors group-hover:text-violet-300">
                          مشاهده در داشبورد
                        </span>
                        <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-1 group-hover:text-violet-300" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="relative z-10 border-t border-violet-500/15">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center">
          <h2 className="text-2xl font-bold tracking-tight lg:text-3xl">
            آماده‌ای همه‌شون رو امتحان کنی؟
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            وارد داشبورد شو و بدون محدودیت، همه‌چیز را تجربه کن.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button asChild size="lg" className="btn-glow gap-2 bg-violet-600 hover:bg-violet-500">
              <Link href="/dashboard">
                ورود به داشبورد
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="gap-2 border-violet-500/40 hover:bg-violet-600/10">
              <Link href="/">بازگشت به لندینگ</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ── Disclaimer ── */}
      <section className="relative z-10 border-t border-violet-500/20">
        <div className="mx-auto max-w-4xl px-6 py-8">
          <div className="rounded-xl border border-violet-500/20 bg-violet-500/[0.04] p-5 text-center">
            <p className="text-xs leading-relaxed text-muted-foreground">
              این پلتفرم هیچ مسئولیتی در قبال سود یا ضرر شما ندارد. شما تصمیم‌گیرنده‌ی نهایی هستید — ما فقط با آمار و سیگنال‌های متنوع، به شما در گرفتن تصمیم‌های بهتر کمک می‌کنیم.
            </p>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="relative z-10 border-t border-violet-500/20">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-8">
          <div className="flex items-center gap-3">
            <SarvLogo size={32} />
            <div>
              <p className="text-sm font-semibold">SarvBots</p>
              <p className="text-[10px] text-muted-foreground">رشد پایدار سبز</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 SarvBots · همه‌ی حقوق محفوظ است</p>
        </div>
      </footer>
    </div>
  );
}
