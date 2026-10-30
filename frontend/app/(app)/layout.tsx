"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
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
    return <AppShell>{children}</AppShell>;
  }

  if (isLoading || !data) return spinner;
  

  return <AppShell>{children}</AppShell>;
}
