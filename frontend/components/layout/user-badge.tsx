"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { LogOut, User, Sparkles, UserPlus, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLogout } from "@/lib/queries";
import { getUserInfo, getUserToken, type StoredUser } from "@/lib/auth";

export function UserBadge() {
  const [user, setUser] = useState<StoredUser | null>(null);
  const [mounted, setMounted] = useState(false);
  const logout = useLogout();

  useEffect(() => {
    setMounted(true);
    setUser(getUserInfo());
  }, []);

  // قبل از mount (SSR) → placeholder
  if (!mounted) {
    return <div className="h-8 w-24" />;
  }

  const hasToken = getUserToken();
  const isLoggedIn = !!hasToken;

  // ─── کاربر لاگین‌شده ───
  if (isLoggedIn) {
    return (
      <div className="flex w-full flex-col gap-2">
        <Badge
          variant="outline"
          className="justify-center gap-2 border-emerald-500/40 bg-emerald-600/10 py-2 text-emerald-300"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          <User className="h-3 w-3" />
          <span className="truncate text-[10px]" dir="ltr">
            {user?.email ?? "کاربر"}
          </span>
        </Badge>
        <Button
          asChild
          size="sm"
          variant="outline"
          className="w-full justify-center gap-2 border-violet-500/30 text-violet-300 hover:bg-violet-500/10"
        >
          <Link href="/settings">
            <Settings className="h-3.5 w-3.5" />
            تنظیمات
          </Link>
        </Button>
        <Button
          onClick={logout}
          size="sm"
          variant="outline"
          className="w-full justify-center gap-2 border-rose-500/30 text-rose-300 hover:bg-rose-500/10"
        >
          <LogOut className="h-3.5 w-3.5" />
          خروج
        </Button>
      </div>
    );
  }

  // ─── مهمان ───
  return (
    <div className="flex w-full flex-col gap-2">
      <Badge
        variant="outline"
        className="justify-center gap-2 border-violet-500/40 bg-violet-600/10 py-2 text-violet-300"
      >
        <Sparkles className="h-3 w-3" />
        حالت مهمان
      </Badge>
      <Button
        asChild
        size="sm"
        className="w-full justify-center gap-2 bg-violet-600 hover:bg-violet-500"
      >
        <Link href="/register">
          <UserPlus className="h-3.5 w-3.5" />
          ثبت‌نام
        </Link>
      </Button>
    </div>
  );
}
