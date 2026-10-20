"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { User, Shield, Key, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/settings", label: "پروفایل", icon: User },
  { href: "/settings/security", label: "امنیت حساب", icon: Shield },
  { href: "/settings/wallex", label: "اتصال به والکس", icon: Key },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="mx-auto max-w-5xl p-4 md:p-6 lg:p-8">
      <div className="mb-8">
        <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1 mb-4 transition-colors">
          <ArrowRight className="h-4 w-4" /> بازگشت به داشبورد
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">تنظیمات</h1>
        <p className="text-muted-foreground mt-1">مدیریت حساب کاربری و اتصالات شما</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* منوی تب‌ها */}
        <nav className="flex md:flex-col gap-2 overflow-x-auto md:w-64 shrink-0 pb-4 md:pb-0">
          {tabs.map((tab) => {
            const isActive = pathname === tab.href || (tab.href !== "/settings" && pathname.startsWith(tab.href));
            const Icon = tab.icon;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap",
                  isActive
                    ? "bg-violet-600/10 text-violet-400"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </Link>
            );
          })}
        </nav>

        {/* محتوای تب فعال */}
        <div className="flex-1 min-w-0">
          {children}
        </div>
      </div>
    </div>
  );
}
