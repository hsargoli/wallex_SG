"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { getUserToken } from "@/lib/auth";
import { useWallexStatus } from "@/lib/queries";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  // useWallexStatus خودش enabled: !!getUserToken() داره
  const { data, isLoading } = useWallexStatus();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    // ۱. بدون JWT → /login
    const hasToken = !!getUserToken();
    if (!hasToken) {
      router.replace("/login");
      return;
    }

    // ۲. صفحه‌ی settings/wallex مستثنی (وگرنه loop)
    if (pathname === "/settings/wallex") return;

    // ۳. Wallex disconnected → /settings/wallex
    if (!isLoading && data && !data.connected) {
      router.replace("/settings/wallex");
    }
  }, [mounted, pathname, data, isLoading, router]);

  // spinner helper
  const spinner = (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
    </div>
  );

  // ۱. SSR / قبل از mount
  if (!mounted) return spinner;

  // ۲. بدون JWT → effect در حال redirect به /login
  if (!getUserToken()) return spinner;

  // ۳. صفحه settings/wallex مستثنی — نیازی به چک Wallex نیست
  if (pathname === "/settings/wallex") {
    return <AppShell>{children}</AppShell>;
  }

  // ۴. isLoading یا داده نیامده → spinner (جلوگیری از flash داشبورد)
  if (isLoading || !data) return spinner;

  // ۵. disconnected → effect در حال redirect به /settings/wallex
  if (!data.connected) return spinner;

  // ۶. اوکی
  return <AppShell>{children}</AppShell>;
}
