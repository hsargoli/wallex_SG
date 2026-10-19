"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowRight, Eye, EyeOff, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { useResetPassword } from "@/lib/queries";
import { toast } from "sonner";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const reset = useResetPassword();

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) { toast.error("توکن یافت نشد."); return; }
    if (password.length < 8) { toast.error("رمز باید حداقل ۸ کاراکتر باشد."); return; }
    reset.mutate({ token, new_password: password }, {
      onSuccess: () => {
        toast.success("رمز عبور با موفقیت تغییر کرد.");
        setTimeout(() => router.push("/login"), 2000);
      },
      onError: () => toast.error("توکن نامعتبر یا منقضی شده است."),
    });
  };

  if (!token) {
    return (
      <div className="rounded-2xl border border-rose-500/30 bg-card p-6 text-center shadow-xl">
        <p className="text-sm text-rose-400">لینک بازیابی نامعتبر است.</p>
        <Link href="/forgot-password" className="mt-4 block text-sm text-emerald-400 hover:underline">درخواست لینک جدید</Link>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="rounded-2xl border border-border bg-card/95 p-8 shadow-2xl backdrop-blur-md">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="password">رمز عبور جدید</Label>
          <div className="relative">
            <Lock className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input 
              id="password" 
              type={showPwd ? "text" : "password"} 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              dir="ltr" 
              className="pl-10 pr-9 font-mono text-sm bg-background" 
              required 
            />
            <button 
              type="button" 
              onClick={() => setShowPwd((s) => !s)} 
              className="absolute left-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
        <Button type="submit" disabled={reset.isPending} className="w-full bg-emerald-600 hover:bg-emerald-500 h-11 text-base">
          {reset.isPending ? "در حال ذخیره..." : "تغییر رمز عبور"}
        </Button>
      </div>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <>
      <BackgroundFX />
      <div className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-[400px] space-y-6">
          <div className="text-center flex flex-col items-center">
            <SarvLogo size={56} />
            <h1 className="mt-4 text-2xl font-bold tracking-tight">تعیین رمز عبور جدید</h1>
            <p className="mt-2 text-sm text-muted-foreground">لطفاً رمز عبور جدید خود را وارد کنید.</p>
          </div>
          <Suspense fallback={<p className="text-center text-sm">در حال بارگذاری...</p>}>
            <ResetPasswordForm />
          </Suspense>
          <div className="text-center text-sm">
            <Link href="/login" className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors">
              <ArrowRight className="h-4 w-4" /> بازگشت به صفحه ورود
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
