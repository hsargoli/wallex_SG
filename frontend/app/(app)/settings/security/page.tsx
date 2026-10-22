"use client";

import { useState } from "react";
import { Key, ShieldAlert, LogOut, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { toast } from "sonner";
import { useChangePassword, useLogoutAll } from "@/lib/queries";

export default function SecuritySettingsPage() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  const changePasswordMut = useChangePassword();
  const logoutAllMut = useLogoutAll();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword.length < 8) {
      toast.error("رمز عبور جدید باید حداقل ۸ کاراکتر باشد.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("رمز عبور جدید و تکرار آن یکسان نیستند.");
      return;
    }

    changePasswordMut.mutate(
      { old_password: oldPassword, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success("رمز عبور با موفقیت تغییر یافت. لطفاً دوباره وارد شوید.");
          setOldPassword("");
          setNewPassword("");
          setConfirmPassword("");
        },
        onError: (err: any) => {
          const msg = err.response?.data?.detail || "خطا در تغییر رمز عبور";
          toast.error(msg);
        },
      }
    );
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      
      {/* Change Password Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Key className="h-5 w-5 text-amber-400" /> تغییر رمز عبور
          </CardTitle>
          <CardDescription>
            برای حفظ امنیت حساب، از یک رمز عبور قوی و منحصر به فرد استفاده کنید.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="old">رمز عبور فعلی</Label>
              <Input 
                id="old" 
                type="password" 
                value={oldPassword} 
                onChange={(e) => setOldPassword(e.target.value)} 
                required 
                dir="ltr" 
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="new">رمز عبور جدید</Label>
              <Input 
                id="new" 
                type="password" 
                value={newPassword} 
                onChange={(e) => setNewPassword(e.target.value)} 
                required 
                dir="ltr" 
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm">تکرار رمز عبور جدید</Label>
              <Input 
                id="confirm" 
                type="password" 
                value={confirmPassword} 
                onChange={(e) => setConfirmPassword(e.target.value)} 
                required 
                dir="ltr" 
              />
            </div>

            <Button 
              type="submit" 
              disabled={changePasswordMut.isPending} 
              className="w-full bg-violet-600 hover:bg-violet-500 text-white"
            >
              {changePasswordMut.isPending ? "در حال ذخیره..." : "تغییر رمز عبور"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Session Management Card */}
      <Card className="border-rose-500/20 bg-rose-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg text-rose-400">
            <ShieldAlert className="h-5 w-5" /> مدیریت نشست‌ها
          </CardTitle>
          <CardDescription>
            اگر فکر می‌کنید حساب شما در خطر است یا رمز عبورتان لو رفته، از این بخش استفاده کنید.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-muted-foreground leading-relaxed">
            با کلیک بر روی دکمه زیر، تمام دستگاه‌هایی که با حساب شما وارد شده‌اند (از جمله همین دستگاه) از حساب خارج می‌شوند و توکن‌های آن‌ها باطل می‌گردد.
          </p>
          <Button 
            variant="destructive" 
            className="w-full gap-2"
            disabled={logoutAllMut.isPending}
            onClick={() => {
              if (confirm("آیا مطمئن هستید؟ از تمام دستگاه‌ها خارج خواهید شد.")) {
                logoutAllMut.mutate();
              }
            }}
          >
            <LogOut className="h-4 w-4" />
            {logoutAllMut.isPending ? "در حال خروج..." : "خروج از همه دستگاه‌ها"}
          </Button>
        </CardContent>
      </Card>

    </div>
  );
}
