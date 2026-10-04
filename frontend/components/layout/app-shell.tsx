"use client";

import { cn } from "@/lib/utils";
import { Sidebar } from "./sidebar";
import { SidebarProvider, useSidebar } from "./sidebar-provider";

function ShellContent({ children }: { children: React.ReactNode }) {
  const { collapsed } = useSidebar();

  return (
    <div className="min-h-screen">
      <Sidebar />
      <main
        className={cn(
          "min-h-screen transition-all duration-300",
          collapsed ? "lg:pr-16" : "lg:pr-64",
        )}
      >
        <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
      </main>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <ShellContent>{children}</ShellContent>
    </SidebarProvider>
  );
}
