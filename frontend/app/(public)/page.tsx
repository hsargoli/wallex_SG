import Link from "next/link";
import { Bot, BarChart3, Radar, Zap, ArrowLeft, Sparkles, FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LiveChartDynamic } from "@/components/landing/live-chart-dynamic";
import { BackgroundFX } from "@/components/landing/background-fx";
import { TickerTape } from "@/components/landing/ticker-tape";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { LandingAuthButton } from "@/components/landing/landing-auth-button";
import { TiltCard } from "@/components/landing/tilt-card";

const FEATURES = [
  { icon: Bot,       title: "ربات‌های معاملاتی", desc: "استراتژی‌های هوشمند برای شرایط مختلف بازار" },
  { icon: BarChart3, title: "تحلیل زنده",      desc: "رژیم بازار، شخصیت ارز، و سیگنال‌های لحظه‌ای" },
  { icon: Radar,     title: "اسکنر بازار",     desc: "پیدا کردن فرصت‌ها در صدها نماد، در چند ثانیه" },
  { icon: Zap,       title: "سیگنال‌ها",        desc: "نقاط ورود و خروج، با تأییدیه‌ی چندلایه" },
];

export default function LandingPage() {
  return (
    <div className="dark relative min-h-screen overflow-hidden bg-background text-foreground">
      <BackgroundFX />

      {/* HERO */}
      <section className="relative z-10">
        <div className="mx-auto max-w-7xl px-6 pb-10 pt-16 lg:pt-24">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div className="space-y-6">
              <Badge variant="outline" className="gap-2 border-violet-500/40 bg-violet-600/10 text-violet-300">
                <Sparkles className="h-3 w-3" /> نسخه‌ی آزمایشی
              </Badge>

              <div className="flex items-center gap-4">
                <SarvLogo size={64} />
                <h1 className="text-5xl font-bold tracking-tight lg:text-7xl">
                  <span className="bg-gradient-to-l from-violet-200 via-violet-400 to-purple-600 bg-clip-text text-transparent drop-shadow-[0_0_45px_rgba(139,92,246,0.75)]">
                    SarvBots
                  </span>
                </h1>
              </div>

              <p className="text-xl text-muted-foreground lg:text-2xl">
                ربات‌های معاملاتی هوشمند
              </p>

              <p className="max-w-lg text-base leading-relaxed text-muted-foreground">
                پلتفرم معاملات الگوریتمی روی صرافی والکس. تحلیل زنده،
                سیگنال‌های دقیق، و ربات‌هایی که برای رشد پایدار طراحی شده‌اند.
              </p>

              <div className="flex flex-wrap gap-3 pt-2">
                <LandingAuthButton />
                <Button asChild size="lg" variant="outline" className="gap-2 border-violet-500/40 transition-all duration-300 ease-out hover:-translate-y-1 hover:scale-105 hover:bg-violet-600/10 hover:shadow-[0_10px_40px_-10px_rgba(139,92,246,0.5)]">
                  <Link href="/guest">ورود مهمان (Guest Trade)</Link>
                </Button>
              </div>
            </div>

            <div className="float-y">
              <LiveChartDynamic className="w-full" />
            </div>
          </div>
        </div>
      </section>

      <div className="relative z-10">
        <TickerTape />
      </div>

      <section className="relative z-10">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="mb-10 text-center">
            <h2 className="text-2xl font-bold tracking-tight lg:text-3xl">یک پلتفرم، همه‌چیز</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              از تحلیل تا معامله — بدون جابه‌جایی بین چند ابزار
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <Card key={f.title}
                    className="border-violet-500/15 bg-background/60 backdrop-blur-sm transition hover:-translate-y-1 hover:border-violet-500/50 hover:bg-violet-600/10">
                <CardContent className="space-y-3 p-6">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/40 to-fuchsia-600/10">
                    <f.icon className="h-5 w-5 text-violet-300" />
                  </div>
                  <h3 className="text-sm font-semibold">{f.title}</h3>
                  <p className="text-xs leading-relaxed text-muted-foreground">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="relative z-10 border-t border-violet-500/20">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center">
          <h2 className="text-2xl font-bold tracking-tight lg:text-3xl">آماده‌ای شروع کنی؟</h2>
          <p className="mt-3 text-sm text-muted-foreground">
            بدون ثبت‌نام، محیط دمو را ببین. هر وقت خواستی، وارد داشبورد شو.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <LandingAuthButton />
            <Button asChild size="lg" variant="outline" className="gap-2 border-violet-500/40 transition-all duration-300 ease-out hover:-translate-y-1 hover:scale-105 hover:bg-violet-600/10 hover:shadow-[0_10px_40px_-10px_rgba(139,92,246,0.5)]">
              <Link href="/guest">ورود مهمان (Guest Trade)</Link>
            </Button>
          </div>
        </div>
      </section>


      {/* DEMO SECTION */}
      <section className="relative z-10 px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <TiltCard className="group relative w-full rounded-xl border border-violet-500/30 bg-violet-950/20 hover:shadow-[0_20px_60px_-15px_rgba(139,92,246,0.6)]">
            <Card className="border-0 bg-transparent">
            <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            <CardContent className="relative flex flex-col items-center gap-6 p-10 text-center overflow-hidden">
              {/* هاله نورانی پشت کارت */}
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-violet-600/20 via-transparent to-transparent opacity-50 blur-2xl transition-opacity duration-500 group-hover:opacity-100 pointer-events-none" />

              {/* آیکون با هاله نور */}
              <div className="relative rounded-2xl bg-violet-600/30 p-4 shadow-[0_0_30px_rgba(139,92,246,0.3)] transition-transform duration-300 group-hover:scale-110 group-hover:shadow-[0_0_50px_rgba(139,92,246,0.6)] z-10">
                <FlaskConical className="h-10 w-10 text-violet-300" />
              </div>

              {/* عنوان با افکت درخشش */}
              <div className="relative z-10">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Sparkles className="h-5 w-5 text-violet-400 animate-pulse" />
                  <h2 className="text-3xl font-extrabold text-white drop-shadow-[0_0_15px_rgba(139,92,246,0.8)]">
                    دموی تعاملی SarvBots
                  </h2>
                  <Sparkles className="h-5 w-5 text-violet-400 animate-pulse" />
                </div>
                <p className="mt-3 text-base text-muted-foreground leading-relaxed max-w-2xl mx-auto">
                  محیط این پلتفرم را نگاهی بیندازید و ببینید این پلتفرم چه ویژگی‌هایی دارد.
                </p>
                
                {/* لیست قابلیت‌های قابل مشاهده در دمو (CTA) */}
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  <Badge variant="outline" className="border-violet-500/30 bg-violet-500/10 text-violet-200">⚡ سیگنال‌های زنده</Badge>
                  <Badge variant="outline" className="border-violet-500/30 bg-violet-500/10 text-violet-200">🔍 اسکنر بازار</Badge>
                  <Badge variant="outline" className="border-violet-500/30 bg-violet-500/10 text-violet-200">🧠 شخصیت ارزها</Badge>
                  <Badge variant="outline" className="border-violet-500/30 bg-violet-500/10 text-violet-200">🤖 ربات‌های معاملاتی</Badge>
                </div>
              </div>

              {/* دکمه با گرادیان و درخشش */}
              <Button asChild size="lg" className="relative z-10 mt-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 transition-all duration-300 ease-out group-hover:-translate-y-1 group-hover:shadow-[0_10px_40px_-10px_rgba(192,38,211,0.8)] border border-violet-400/50">
                <Link href="/demo">
                  مشاهده دموی زنده
                  <ArrowLeft className="h-5 w-5 mr-2 animate-bounce-x" />
                </Link>
              </Button>
            </CardContent>
          </Card>
          </TiltCard>
        </div>
      </section>

      <footer className="relative z-10 border-t border-violet-500/20 bg-black/40 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 py-8 md:flex-row">
          <div className="flex items-center gap-3">
            <SarvLogo size={32} />
            <div>
              <p className="text-sm font-semibold">SarvBots</p>
              <p className="text-[10px] text-muted-foreground">رشد پایدار سبز</p>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
            <Link href="/terms" className="transition-colors hover:text-violet-400">قوانین و مقررات</Link>
            <Link href="/privacy" className="transition-colors hover:text-violet-400">حریم خصوصی</Link>
            <Link href="/risk" className="transition-colors hover:text-violet-400">سلب مسئولیت</Link>
          </div>

          <p className="text-xs text-muted-foreground">© 2026 SarvBots · همه‌ی حقوق محفوظ است</p>
        </div>
      </footer>
    </div>
  );
}
