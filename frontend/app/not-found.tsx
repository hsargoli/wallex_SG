import Link from "next/link";
import { Home, Search } from "lucide-react";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-4 rounded-lg border p-6 text-center">
        <p className="text-muted-foreground text-6xl font-bold">۴۰۴</p>
        <h1 className="text-xl font-bold">صفحه پیدا نشد</h1>
        <p className="text-muted-foreground text-sm leading-6">
          آدرسی که دنبالش بودید در این پلتفرم وجود ندارد. ممکن است حذف شده
          باشد یا آدرس اشتباه تایپ شده باشد.
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <Link
            href="/"
            className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-1 rounded-md px-4 py-2 text-sm font-medium"
          >
            <Home className="h-4 w-4" /> صفحه اصلی
          </Link>
          <Link
            href="/markets"
            className="border-border hover:bg-muted inline-flex items-center gap-1 rounded-md border px-4 py-2 text-sm font-medium"
          >
            <Search className="h-4 w-4" /> بازارها
          </Link>
        </div>
      </div>
    </main>
  );
}
