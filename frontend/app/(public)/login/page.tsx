"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Eye, EyeOff, Lock, LogIn, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { useLogin } from "@/lib/queries";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  const canSubmit = email.trim().length > 3 && password.length > 0 && !login.isPending;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    login.mutate(
      { email: email.trim(), password },
      {
        onSuccess: () => {
          // layout (app) خودش redirect می‌کنه اگه Wallex disconnected باشه
          router.push("/dashboard");
        },
      },
    );
  };

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

      <section className="relative z-10 mx-auto max-w-md px-6 py-16">
        <div className="text-center">
          <div className="mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/40 to-fuchsia-600/10">
            <LogIn className="h-6 w-6 text-violet-300" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            <span className="bg-gradient-to-l from-violet-200 via-violet-400 to-purple-600 bg-clip-text text-transparent drop-shadow-[0_0_25px_rgba(139,92,246,0.5)]">
              ورود
            </span>
          </h1>
          <p className="mt-3 text-sm text-muted-foreground">
            به حساب SarvBots خودت وارد شو
          </p>
        </div>

        <form onSubmit={onSubmit} className="mt-8 space-y-4">
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
              className="h-11 bg-background/60 font-mono text-sm"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="password" className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Lock className="h-3.5 w-3.5" />
                پسورد
              </Label>
              <Link href="/forgot-password" className="text-[11px] text-violet-400 hover:text-violet-300 hover:underline transition-colors">
                فراموشی رمز عبور؟
              </Link>
            </div>
            <div className="relative">
              <Input
                id="password"
                type={showPwd ? "text" : "password"}
                autoComplete="current-password"
                placeholder="پسورد"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 bg-background/60 pl-10 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            disabled={!canSubmit}
            className="btn-glow h-11 w-full gap-2 bg-violet-600 hover:bg-violet-500"
          >
            {login.isPending ? "در حال ورود..." : (
              <>
                ورود
                <ArrowLeft className="h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        <div className="mt-6 flex flex-col items-center gap-3">
          <p className="text-center text-xs text-muted-foreground">
            حساب نداری؟{" "}
            <Link href="/register" className="font-semibold text-violet-300 hover:underline">
              ثبت‌نام کن
            </Link>
          </p>
          <p className="text-center text-[10px] text-muted-foreground/60">
            اگه فعلاً ثبت‌نام نمی‌خوای،{" "}
            <Link href="/demo" className="font-medium text-violet-400/80 transition-colors hover:text-violet-300 hover:underline">
              دموی محیط (مهمان)
            </Link>{" "}
            رو ببین.
          </p>
        </div>
      </section>

            <footer className="relative z-10 mt-auto border-t border-violet-500/20 bg-black/40 backdrop-blur-md">
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
