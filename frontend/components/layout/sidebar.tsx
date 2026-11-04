"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { Globe, LayoutDashboard, Wallet, TrendingUp, Calculator, Activity, PieChart, Zap, Radar, Bot, Play, ClipboardList, Menu, X, ChevronLeft, ChevronRight, FlaskConical, SquarePen, Brain, TrendingDown, Settings } from "lucide-react";
import { UserBadge } from "./user-badge";
import { cn } from "@/lib/utils";
import { useHealth } from "@/lib/queries";
import { useSidebar } from "./sidebar-provider";
import { ThemeSwitcher } from "./theme-switcher";

type NavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  desc: string;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

const navGroups: NavGroup[] = [
  {
    label: "نمای کلی",
    items: [
      { href: "/dashboard", label: "داشبورد", icon: LayoutDashboard, desc: "نمای کلی بازار و وضعیت ربات" },
    ],
  },
  {
    label: "کشف فرصت",
    items: [
      { href: "/markets", label: "بازارها", icon: TrendingUp, desc: "قیمت لحظه‌ای رمزارزها" },
      { href: "/scanner", label: "اسکنر بازار", icon: Radar, desc: "پیدا کردن فرصت‌ها" },
      { href: "/signals", label: "سیگنال‌ها", icon: Zap, desc: "سیگنال‌های معاملاتی" },
      { href: "/keyhan", label: "کیهان بازار", icon: Globe, desc: "نمای کهکشانی بازار" },
    ],
  },
  {
    label: "9",
    items: [
      { href: "/analysis", label: "شخصیت ارز", icon: Brain, desc: "تحلیل رژیم و رفتار هر نماد" },
      { href: "/nooaah", label: "ربات نوح", icon: Bot, desc: "ربات انتخاب بهترین نماد + بک‌تست" },
      { href: "/bear-hunter", label: "شکارچی خرس", icon: TrendingDown, desc: "ربات short در بازار نزولی" },
    ],
  },
  {
    label: "ربات‌ها و آزمون",
    items: [
      { href: "/bots", label: "ربات‌ها", icon: Bot, desc: "ربات‌های معاملاتی" },
      { href: "/backtest", label: "بک‌تست", icon: FlaskConical, desc: "تست ربات روی داده‌ی گذشته" },
      { href: "/paper-trading", label: "Paper ربات‌ها", icon: Play, desc: "تست ربات‌های معاملاتی در Paper Mode" },
      { href: "/paper-trading/manual", label: "تست دستی", icon: SquarePen, desc: "ثبت سفارش دستی در Paper (بدون ریسک)" },
    ],
  },
  {
    label: "معامله و دارایی",
    items: [
      { href: "/order-bot", label: "ثبت سفارش دستی", icon: SquarePen, desc: "ثبت دستی سفارش روی والکس" },
      { href: "/profitability", label: "سودآوری", icon: Calculator, desc: "محاسبه‌ی سود و زیان پیش از معامله" },
      { href: "/orders", label: "سفارش‌ها", icon: ClipboardList, desc: "تاریخچه و سفارش‌های باز" },
      { href: "/portfolio", label: "سبد دارایی", icon: PieChart, desc: "دارایی‌های فعلی شما" },
      { href: "/bot-wallet", label: "کیف پول ربات", icon: Wallet, desc: "مدیریت بودجه‌ی ربات‌ها" },
    ],
  },
  {
    label: "پژوهش و تحلیل",
    items: [
      { href: "/research/tsfresh", label: "تحلیل تشابه BTC", icon: FlaskConical, desc: "شباهت تاریخی الگوها" },
      { href: "/research/regime-accuracy", label: "دقت تشخیص رژیم", icon: Activity, desc: "دقت SarvRouter" },
      { href: "/research/sarvrouter-timeline", label: "تاریخچه تصمیمات", icon: ClipboardList, desc: "تاریخچه ۲,۲۳۷ تصمیم" },
    ],
  },
];

function computeActiveHref(pathname: string, groups: NavGroup[]): string | null {
  // Longest-prefix-match: /paper-trading/manual should win over /paper-trading
  const matches = groups
    .flatMap((g) => g.items)
    .filter((item) =>
      item.href === "/"
        ? pathname === "/"
        : pathname === item.href || pathname.startsWith(item.href + "/"),
    )
    .sort((a, b) => b.href.length - a.href.length);
  return matches[0]?.href ?? null;
}

export function Sidebar() {
  const pathname = usePathname();
  const activeHref = computeActiveHref(pathname, navGroups);
  const health = useHealth();
  const isOnline = health.isSuccess && health.data?.status === "ok";

  const { collapsed, toggle, mobileOpen, setMobileOpen } = useSidebar();

  // Auto-close mobile on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname, setMobileOpen]);

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className={cn(
          "fixed top-4 z-30 flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background/80 backdrop-blur transition-all lg:hidden",
          "right-4",
        )}
        aria-label="باز کردن منو"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 flex h-screen flex-col border-l border-border bg-sidebar transition-all duration-300",
          // Mobile width always full; Desktop toggles
          collapsed ? "w-64 lg:w-16" : "w-64",
          // Mobile slide in/out
          mobileOpen ? "translate-x-0" : "translate-x-full lg:translate-x-0",
        )}
      >
        {/* Header */}
        <div className="flex h-16 items-center gap-2.5 border-b border-border px-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-sidebar-primary to-sidebar-primary/60 shadow-lg shadow-sidebar-primary/30">
            <Activity className="h-4 w-4 text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-sm font-bold tracking-tight">
                SarvBots
              </h1>
              <p className="truncate text-[10px] text-sidebar-foreground/60">
                Micro-Scalping v0.1
              </p>
            </div>
          )}
          {/* Collapse toggle (desktop only) */}
          <button
            onClick={toggle}
            className="sidebar-toggle hidden shrink-0 lg:flex"
            aria-label={collapsed ? "باز کردن سایدبار" : "جمع کردن سایدبار"}
            title={collapsed ? "باز کردن" : "جمع کردن"}
          >
            {collapsed ? (
              <ChevronLeft className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>

          {/* Close button (mobile only) */}
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded-md p-1.5 hover:bg-white/5 lg:hidden"
            aria-label="بستن منو"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 space-y-4 overflow-y-auto px-2 py-3">
          {navGroups.map((group, gi) => (
            <div key={group.label} className="space-y-0.5">
              {/* Group label */}
              {!collapsed && (
                <p className="px-3 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wider text-sidebar-foreground/40">
                  {group.label}
                </p>
              )}
              {/* Collapsed: divider */}
              {collapsed && gi > 0 && (
                <div className="mx-3 mb-2 border-t border-sidebar-border/50" />
              )}
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = item.href === activeHref;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    className={cn(
                      "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                      collapsed && "lg:justify-center lg:px-0",
                      active
                        ? "bg-sidebar-primary text-sidebar-primary-foreground font-bold shadow-sm"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && (
                      <span className="truncate font-medium">{item.label}</span>
                    )}
                    {active && !collapsed && (
                      <span className="mr-auto h-1.5 w-1.5 shrink-0 rounded-full bg-sidebar-primary-foreground/70" />
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="relative z-10 space-y-2 border-t border-sidebar-border p-2 pb-16 lg:pb-2">
          {/* Status */}
          <div
            title={collapsed ? (isOnline ? "اتصال برقرار" : "قطع اتصال") : undefined}
            className={cn(
              "flex items-center gap-3 rounded-lg bg-sidebar-accent/40 px-3 py-2",
              collapsed && "lg:justify-center lg:px-0",
            )}
          >
            <div
              className={cn(
                "h-2 w-2 shrink-0 rounded-full",
                isOnline ? "animate-pulse bg-sidebar-primary" : "bg-red-500",
              )}
            />
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-[11px] font-medium text-sidebar-foreground">
                  {isOnline ? "اتصال برقرار" : "قطع اتصال"}
                </p>
                <p className="truncate text-[10px] text-sidebar-foreground/60">
                  {health.isLoading ? "در حال بررسی..." : "Wallex API"}
                </p>
              </div>
            )}
          </div>

          {/* Theme */}
          <div
            className={cn(
              "flex items-center",
              collapsed ? "lg:justify-center" : "justify-end",
            )}
          >
            <ThemeSwitcher />
          </div>
        </div>
        <div className="mt-auto p-4 border-t border-border/50"><UserBadge /></div>
  </aside>
    </>
  );
}
