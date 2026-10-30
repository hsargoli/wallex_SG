"use client";

import Link from "next/link";
import { Heart, ExternalLink } from "lucide-react";

export function SarvFooter() {
  return (
    <footer className="mt-16 border-t border-border/40 py-8">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          {/* Story (کم‌رنگ) */}
          <div className="max-w-md text-xs text-muted-foreground leading-relaxed">
            <p className="mb-2 flex items-center gap-1 font-medium text-foreground/80">
              <Heart className="h-3 w-3 text-rose-400" />
              داستان سروباتس
            </p>
            <p>
              سروباتس از یک سؤال ساده شروع شد: «چرا کاربر نباید بداند ربات
              چطور فکر می‌کند؟» ما تصمیم گرفتیم شفاف باشیم — هر ربات، backtest،
              و وضعیت زنده‌اش را نشان بدهیم. این پلتفرم، برای کسانی است که
              می‌خواهند <b>بفهمند</b>، نه فقط دنبال کنند.
            </p>
          </div>

          {/* Links */}
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
            <div className="space-y-1.5">
              <p className="font-medium text-foreground/80">محصول</p>
              <Link href="/learn" className="block text-muted-foreground hover:text-emerald-400">
                آموزش
              </Link>
              <Link href="/bots" className="block text-muted-foreground hover:text-emerald-400">
                ربات‌ها
              </Link>
              <Link href="/backtest" className="block text-muted-foreground hover:text-emerald-400">
                Backtest
              </Link>
              <Link href="/paper-trading" className="block text-muted-foreground hover:text-emerald-400">
                Paper Trading
              </Link>
            </div>
            <div className="space-y-1.5">
              <p className="font-medium text-foreground/80">حقوقی</p>
              <Link href="/terms" className="block text-muted-foreground hover:text-emerald-400">
                قوانین
              </Link>
              <Link href="/privacy" className="block text-muted-foreground hover:text-emerald-400">
                حریم خصوصی
              </Link>
              <Link href="/risk" className="block text-muted-foreground hover:text-emerald-400">
                سلب مسئولیت
              </Link>
              <a
                href="https://github.com/hsargoli/wallex_SG"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-muted-foreground hover:text-emerald-400"
              >
                GitHub <ExternalLink className="h-2.5 w-2.5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-6 border-t border-border/20 pt-4 text-center text-[10px] text-muted-foreground/70">
          © ۱۴۰۵ سروباتس — ساخته‌شده با دقت، شاهد، و مهربانی.
        </div>
      </div>
    </footer>
  );
}
