"use client";

import { useEffect, useState } from "react";
import { User as UserIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getUserInfo, type StoredUser } from "@/lib/auth";

export default function ProfileSettingsPage() {
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {
    setUser(getUserInfo());
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <UserIcon className="h-5 w-5 text-violet-400" /> اطلاعات پروفایل
        </CardTitle>
        <CardDescription>اطلاعات پایه حساب کاربری شما.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>ایمیل</Label>
          <Input value={user?.email ?? "در حال بارگذاری..."} disabled dir="ltr" className="bg-muted" />
          <p className="text-xs text-muted-foreground">ایمیل شما به عنوان شناسه حساب استفاده می‌شود و قابل تغییر نیست.</p>
        </div>
        
        <div className="space-y-2 pt-4">
          <Label>نام نمایشی (به زودی)</Label>
          <Input disabled placeholder="این قابلیت به زودی اضافه می‌شود" />
        </div>
      </CardContent>
    </Card>
  );
}
