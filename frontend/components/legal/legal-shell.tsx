import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function LegalShell({
  title,
  updatedAt,
  children,
}: {
  title: string;
  updatedAt: string;
  children: React.ReactNode;
}) {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-10">
      <Link
        href="/"
        className="text-muted-foreground hover:text-foreground mb-6 inline-flex items-center gap-1 text-sm"
      >
        <ArrowRight className="h-4 w-4" />
        بازگشت به صفحه اصلی
      </Link>

      <header className="mb-8 border-b pb-6">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-muted-foreground mt-2 text-xs">
          آخرین به‌روزرسانی: {updatedAt}
        </p>
      </header>

      <article className="space-y-6 text-sm leading-7 [&_h2]:mt-8 [&_h2]:mb-3 [&_h2]:text-base [&_h2]:font-bold [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pr-6">
        {children}
      </article>

      <footer className="mt-12 border-t pt-6 text-xs text-muted-foreground">
        <p className="mb-3">
          با استفاده از این پلتفرم، می‌پذیرید که معاملات ارز دیجیتال
          ریسک بالا دارد و مسئولیت تصمیم‌های مالی بر عهده‌ی شماست.
        </p>
        <nav className="flex flex-wrap gap-x-4 gap-y-2">
          <Link href="/terms" className="hover:text-foreground">شرایط استفاده</Link>
          <Link href="/privacy" className="hover:text-foreground">حریم خصوصی</Link>
          <Link href="/risk" className="hover:text-foreground">هشدار ریسک</Link>
        </nav>
      </footer>
    </main>
  );
}
