"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getUserToken } from "@/lib/auth";

export function LandingAuthButton() {
  const [mounted, setMounted] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsLoggedIn(!!getUserToken());
  }, []);

  const baseClasses = "btn-glow gap-2 transition-all duration-300 ease-out hover:-translate-y-1 hover:scale-105";

  // در زمان لود اولیه (SSR)، یک دکمه پیش‌فرض نشون می‌دیم تا پرش (Flicker) نداشته باشیم
  if (!mounted) {
    return (
      <Button size="lg" className={`${baseClasses} bg-violet-600 hover:bg-violet-500 hover:shadow-[0_15px_50px_-10px_rgba(139,92,246,0.8)]`}>
        <Link href="/login">
          ورود / ثبت‌نام
          <ArrowLeft className="h-4 w-4" />
        </Link>
      </Button>
    );
  }

  if (isLoggedIn) {
    return (
      <Button size="lg" className={`${baseClasses} bg-emerald-600 hover:bg-emerald-500 hover:shadow-[0_15px_50px_-10px_rgba(16,185,129,0.8)]`}>
        <Link href="/dashboard">
          ورود به داشبورد
          <LayoutDashboard className="h-4 w-4" />
        </Link>
      </Button>
    );
  }

  return (
    <Button size="lg" className={`${baseClasses} bg-violet-600 hover:bg-violet-500 hover:shadow-[0_15px_50px_-10px_rgba(139,92,246,0.8)]`}>
      <Link href="/login">
        ورود / ثبت‌نام
        <ArrowLeft className="h-4 w-4" />
      </Link>
    </Button>
  );
}
