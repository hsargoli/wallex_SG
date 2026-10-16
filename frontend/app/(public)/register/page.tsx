import Link from "next/link";
import { ArrowLeft, ArrowRight, Sparkles, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";

export default function RegisterPage() {
  return (
    <div className="dark relative min-h-screen overflow-hidden bg-background text-foreground">
      <BackgroundFX />

      <header className="relative z-10 border-b border-violet-500/15">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <Link href="/" className="flex items-center gap-3 transition hover:opacity-80">
            <SarvLogo size={32} />
            <div>
              <p className="text-sm font-semibold">SarvBots</p>
              <p className="text-[10px] text-muted-foreground">رشد پایدار سبز</p>
            </div>
          </Link>
          <Button asChild size="sm" variant="outline" className="gap-2 border-violet-500/40 hover:bg-violet-600/10">
            <Link href="/">
              <ArrowRight className="h-3.5 w-3.5" />
              بازگشت
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative z-10 mx-auto flex max-w-2xl flex-col items-center px-6 py-16 text-center">
        <Badge variant="outline" className="mb-5 gap-2 border-violet-500/40 bg-violet-600/10 text-violet-300">
          <Sparkles className="h-3 w-3" />
          به‌زودی
        </Badge>

        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/40 to-fuchsia-600/10">
          <UserPlus className="h-7 w-7 text-violet-300" />
        </div>

        <h1 className="text-3xl font-bold tracking-tight lg:text-5xl">
          <span className="bg-gradient-to-l from-violet-200 via-violet-400 to-purple-600 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(139,92,246,0.5)]">
            ثبت‌نام
          </span>
        </h1>

        <p className="mt-5 max-w-xl text-sm leading-relaxed text-muted-foreground lg:text-base">
          در حال ساخت. وقتی آماده شد:
        </p>

        <Card className="mt-6 w-full border-violet-500/20 bg-background/60 backdrop-blur-sm">
          <CardContent className="space-y-3 p-6 text-right">
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                <span>
                  <span className="font-semibold text-violet-300">۳ میلیون تومان</span> پول مجازی
                  (به‌جای ۵۰۰ هزار برای مهمان)
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                <span>دسترسی از همه‌ی دستگاه‌ها (نه فقط این مرورگر)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                <span>حفظ تاریخچه‌ی معاملات شبیه‌سازی</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                <span>امکان اتصال توکن والکس برای ترید واقعی</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button asChild size="lg" className="btn-glow gap-2 bg-violet-600 hover:bg-violet-500">
            <Link href="/guest">
              فعلاً به‌عنوان مهمان ادامه بده
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="gap-2 border-violet-500/40 hover:bg-violet-600/10">
            <Link href="/">بازگشت به لندینگ</Link>
          </Button>
        </div>
      </section>

      <footer className="relative z-10 border-t border-violet-500/20">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <div className="flex items-center gap-3">
            <SarvLogo size={28} />
            <p className="text-xs text-muted-foreground">SarvBots · ثبت‌نام</p>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 SarvBots</p>
        </div>
      </footer>
    </div>
  );
}
