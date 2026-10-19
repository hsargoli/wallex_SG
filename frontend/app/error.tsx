"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, Home, RefreshCw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[GlobalError]", error);
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <div className="border-amber-500/30 bg-amber-500/5 w-full max-w-md space-y-4 rounded-lg border p-6 text-center">
        <AlertTriangle className="text-amber-500 mx-auto h-12 w-12" />
        <h1 className="text-xl font-bold">مشکلی پیش آمد</h1>
        <p className="text-muted-foreground text-sm leading-6">
          متأسفانه در بارگذاری این صفحه خطایی رخ داد. لطفاً دوباره تلاش
          کنید یا به صفحه اصلی بازگردید.
        </p>
        {error.digest && (
          <p className="text-muted-foreground text-xs" dir="ltr">
            کد خطا: {error.digest}
          </p>
        )}
        <div className="flex flex-wrap justify-center gap-2">
          <button
            type="button"
            onClick={reset}
            className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-1 rounded-md px-4 py-2 text-sm font-medium"
          >
            <RefreshCw className="h-4 w-4" /> تلاش دوباره
          </button>
          <Link
            href="/"
            className="border-border hover:bg-muted inline-flex items-center gap-1 rounded-md border px-4 py-2 text-sm font-medium"
          >
            <Home className="h-4 w-4" /> صفحه اصلی
          </Link>
        </div>
      </div>
    </main>
  );
}
