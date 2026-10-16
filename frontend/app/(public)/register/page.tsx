"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft, ArrowRight, Eye, EyeOff, Lock, Mail, Shield, Sparkles,
  UserPlus, Gift, Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { useRegister } from "@/lib/queries";
import { getGuestToken } from "@/lib/guest";
import { cn } from "@/lib/utils";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [mergeGuest, setMergeGuest] = useState(true);

  const guestToken = typeof window !== "undefined" ? getGuestToken() : null;

  const emailOk = EMAIL_RE.test(email.trim());
  const pwdOk = password.length >= 8;
  const confirmOk = confirm.length > 0 && confirm === password;
  const canSubmit = emailOk && pwdOk && confirmOk && !register.isPending;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    register.mutate(
      {
        email: email.trim(),
        password,
        guest_token: mergeGuest && guestToken ? guestToken : null,
      },
      {
        onSuccess: () => {
          router.push("/guest");
        },
      },
    );
  };

  return (
    <div className="dark relative min-h-screen overflow-hidden bg-background text-foreground">
      <BackgroundFX />

      {/* Header */}
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

      <section className="relative z-10 mx-auto max-w-lg px-6 py-12">
        <div className="text-center">
          <div className="mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/40 to-fuchsia-600/10">
            <UserPlus className="h-6 w-6 text-violet-300" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight lg:text-4xl">
            <span className="bg-gradient-to-l from-violet-200 via-violet-400 to-purple-600 bg-clip-text text-transparent drop-shadow-[0_0_25px_rgba(139,92,246,0.5)]">
              ثبت‌نام
            </span>
          </h1>
          <p className="mt-3 text-sm text-muted-foreground">
            ۳ میلیون تومان پول مجازی + دسترسی از همه‌ی دستگاه‌ها
          </p>
        </div>

        {/* بنر merge guest */}
        {guestToken && (
          <Card className="mt-6 border-violet-500/30 bg-violet-600/5 backdrop-blur-sm">
            <CardContent className="flex items-start gap-3 p-4">
              <Gift className="mt-0.5 h-5 w-5 shrink-0 text-violet-300" />
              <div className="flex-1">
                <label className="flex cursor-pointer items-start gap-2">
                  <input
                    type="checkbox"
                    checked={mergeGuest}
                    onChange={(e) => setMergeGuest(e.target.checked)}
                    className="mt-0.5 h-4 w-4 accent-violet-500"
                  />
                  <div>
                    <p className="text-sm font-semibold text-violet-200">
                      دارایی مهمان به این حساب منتقل بشه
                    </p>
                    <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                      پول مجازی + پوزیشن‌های شبیه‌سازی‌شده‌ت به ۳ میلیون اضافه می‌شه.
                    </p>
                  </div>
                </label>
              </div>
            </CardContent>
          </Card>
        )}

        {/* فرم */}
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          {/* ایمیل */}
          <div className="space-y-1.5">
            <Label htmlFor="email" className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Mail className="h-3.5 w-3.5" />
              ایمیل
            </Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={cn(
                "h-11 bg-background/60 font-mono text-sm",
                email && !emailOk && "border-rose-500/50",
              )}
            />
            {email && !emailOk && (
              <p className="text-[10px] text-rose-400">فرمت ایمیل معتبر نیست</p>
            )}
          </div>

          {/* پسورد */}
          <div className="space-y-1.5">
            <Label htmlFor="password" className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Lock className="h-3.5 w-3.5" />
              پسورد
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPwd ? "text" : "password"}
                autoComplete="new-password"
                placeholder="حداقل ۸ کاراکتر"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 bg-background/60 pl-10 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                aria-label={showPwd ? "پنهان کن" : "نمایش بده"}
              >
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {password && !pwdOk && (
              <p className="text-[10px] text-amber-400">
                پسورد باید حداقل ۸ کاراکتر باشه
              </p>
            )}
          </div>

          {/* تکرار پسورد */}
          <div className="space-y-1.5">
            <Label htmlFor="confirm" className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Lock className="h-3.5 w-3.5" />
              تکرار پسورد
            </Label>
            <Input
              id="confirm"
              type={showPwd ? "text" : "password"}
              autoComplete="new-password"
              placeholder="همون پسورد رو دوباره وارد کن"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className={cn(
                "h-11 bg-background/60 font-mono text-sm",
                confirm && !confirmOk && "border-rose-500/50",
              )}
            />
            {confirm && !confirmOk && (
              <p className="text-[10px] text-rose-400">پسوردها یکسان نیستن</p>
            )}
          </div>

          {/* دکمه */}
          <Button
            type="submit"
            disabled={!canSubmit}
            className="btn-glow h-11 w-full gap-2 bg-violet-600 hover:bg-violet-500"
          >
            {register.isPending ? (
              "در حال ثبت‌نام..."
            ) : (
              <>
                ثبت‌نام
                <ArrowLeft className="h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        {/* لینک ورود */}
        <p className="mt-6 text-center text-xs text-muted-foreground">
          حساب داری؟{" "}
          <Link href="/login" className="font-semibold text-violet-300 hover:underline">
            وارد شو
          </Link>
        </p>

        {/* امنیت پسورد */}
        <Card className="mt-6 border-violet-500/15 bg-background/40 backdrop-blur-sm">
          <CardContent className="flex items-start gap-3 p-4">
            <Shield className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
            <div className="text-[11px] leading-relaxed text-muted-foreground">
              <p className="mb-1 font-semibold text-violet-300">چرا پسورد قوی مهمه؟</p>
              <p>
                ما از bcrypt برای ذخیره‌ی پسورد استفاده می‌کنیم — حتی اگه دیتابیس ما هک شه،
                پسوردت قابل خواندن نیست.
              </p>
              <p className="mt-1.5">
                پیشنهاد: یه جمله‌ی طولانی، یا از password manager استفاده کن.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* دکمه مهمان */}
        <div className="mt-6 text-center">
          <Link
            href="/guest"
            className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground transition hover:text-violet-300"
          >
            <Info className="h-3 w-3" />
            فعلاً به‌عنوان مهمان ادامه بده
          </Link>
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
