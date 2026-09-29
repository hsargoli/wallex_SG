"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Wallet,
  TrendingUp,
  Calculator,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useHealth } from "@/lib/queries";

const nav = [
  { href: "/", label: "داشبورد", icon: LayoutDashboard },
  { href: "/budget", label: "بودجه", icon: Wallet },
  { href: "/markets", label: "بازارها", icon: TrendingUp },
  { href: "/profitability", label: "محاسبه سود", icon: Calculator },
];

export function Sidebar() {
  const pathname = usePathname();
  const health = useHealth();
  const isOnline = health.isSuccess && health.data?.status === "ok";

  return (
    <aside className="sticky top-0 flex h-screen w-64 flex-col border-l border-border bg-sidebar">
      <div className="flex items-center gap-3 border-b border-border px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 shadow-lg shadow-emerald-500/20">
          <Activity className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight">Wallex Bot</h1>
          <p className="text-[11px] text-muted-foreground">
            Micro-Scalping v0.1
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {nav.map((item) => {
          const Icon = item.icon;
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all",
                active
                  ? "bg-emerald-500/10 text-emerald-400"
                  : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="font-medium">{item.label}</span>
              {active && (
                <div className="mr-auto h-1.5 w-1.5 rounded-full bg-emerald-400" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2.5">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              isOnline ? "bg-emerald-400 animate-pulse" : "bg-red-500",
            )}
          />
          <div className="flex-1">
            <p className="text-[11px] font-medium">
              {isOnline ? "اتصال برقرار" : "قطع اتصال"}
            </p>
            <p className="text-[10px] text-muted-foreground">
              {health.isLoading ? "در حال بررسی..." : "Wallex API"}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
