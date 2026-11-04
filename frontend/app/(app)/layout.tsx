"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { SarvFooter } from "@/components/layout/sarv-footer";
import { canAccessAppPath, getUserToken } from "@/lib/auth";
import { useWallexStatus } from "@/lib/queries";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  const { data, isLoading } = useWallexStatus();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    // Per Hosein 2026-10-30:
    //   - user token → all app routes ✅
    //   - guest token → only /bots, /bots/[slug] ✅ (SarvRouter/dashboard/... blocked)
    //   - none → /login
    if (!canAccessAppPath(pathname)) {
      router.replace("/login");
      return;
    }

    // در صفحه تنظیمات یا شکارچی خرس، نیازی به ریدایرکت نیست
    if (pathname === "/settings/wallex" || pathname === "/bear-hunter") return;

  }, [mounted, pathname, data, isLoading, router]);

  const spinner = (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
    </div>
  );

  if (!mounted) return spinner;
  if (!canAccessAppPath(pathname)) return spinner;

  if (pathname.startsWith("/settings") || pathname === "/bear-hunter") {
    return <AppShell>{children}<SarvFooter /></AppShell>;
  }

  // Fix (2026-11-04): research pages are insight-only, no auth required
  if (pathname.startsWith("/research/")) {
    return <AppShell>{children}<SarvFooter /></AppShell>;
  }

  // Fix (2026-11-04): don't spin forever on error (e.g. 401 with expired token)
  if (!isLoading && !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
        <p className="text-sm text-muted-foreground">
          اتصال به حساب برقرار نشد (احتمالاً توکن منقضی شده).
        </p>
        <a href="/login" className="text-sm text-primary underline">
          ورود مجدد
        </a>
      </div>
    );
  }

  if (isLoading) return spinner;
  

  return <AppShell>{children}</AppShell>;
}
