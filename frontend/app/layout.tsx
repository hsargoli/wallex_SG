import type { Metadata } from "next";
import "@fontsource/vazirmatn/400.css";
import "@fontsource/vazirmatn/500.css";
import "@fontsource/vazirmatn/700.css";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/layout/sidebar";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "Wallex Trading Bot",
  description: "داشبورد مدیریت ربات معاملاتی والکس",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="fa"
      dir="rtl"
      className="dark h-full antialiased"
      style={{ fontFamily: "Vazirmatn, system-ui, sans-serif" }}
    >
      <body className="min-h-full bg-background text-foreground">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
              <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
            </main>
          </div>
          <Toaster position="top-center" richColors />
        </Providers>
      </body>
    </html>
  );
}
