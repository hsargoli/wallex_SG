"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Key, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { api } from "@/lib/api";

export default function SecuritySettingsPage() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isPending, setIsPending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error("رمز عبور جدید باید حداقل ۸ کاراکتر باشد");
      return;
    }
    setIsPending(true);
    try {
      await api.changePassword(oldPassword, newPassword);
      toast.success("رمز عبور با موفقیت تغییر کرد.");
      setOldPassword("");
      setNewPassword("");
    } catch (err: any) {
      const msg = err.response?.data?.detail || "خطا در تغییر رمز عبور";
      toast.error(msg);
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Key className="h-5 w-5 text-amber-400" /> تغییر رمز عبور
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="old">رمز عبور فعلی</Label>
              <Input id="old" type="password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} required dir="ltr" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new">رمز عبور جدید</Label>
              <Input id="new" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required dir="ltr" />
            </div>
            <Button type="submit" disabled={isPending} className="w-full">
              {isPending ? "در حال ذخیره..." : "تغییر رمز عبور"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
