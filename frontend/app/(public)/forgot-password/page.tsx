"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BackgroundFX } from "@/components/landing/background-fx";
import { SarvLogo } from "@/components/landing/sarv-logo";
import { useForgotPassword } from "@/lib/queries";
import { toast } from "sonner";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const forgot = useForgotPassword();

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    forgot.mutate(email.trim(), {
      onSuccess: () => toast.success("ایمیل بازیابی ارسال شد. صندوق ورودی خود را چک کنید."),
      onError: () => toast.error("خطا در ارسال ایمیل."),
    });
  };

  return (
    <>
      <BackgroundFX />
      <div className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-[400px] space-y-6">
          <div className="text-center flex flex-col items-center">
            <SarvLogo className="h-14 w-14 text-emerald-400 drop-shadow-[0_0_15px_rgba(52,211,153,0.3)]" />
            <h1 className="mt-4 text-2xl font-bold tracking-tight">فراموشی رمز عبور</h1>
            <p className="mt-2 text-sm text-muted-foreground">ایمیل خود را وارد کنید تا لینک بازیابی ارسال شود.</p>
          </div>

          <form onSubmit={onSubmit} className="rounded-2xl border border-border bg-card/95 p-8 shadow-2xl backdrop-blur-md">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">ایمیل</Label>
                <div className="relative">
                  <Mail className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input 
                    id="email" 
                    type="email" 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)} 
                    placeholder="example@email.com" 
                    dir="ltr" 
                    className="pl-3 pr-9 font-mono text-sm bg-background" 
                    required 
                  />
                </div>
              </div>
              <Button type="submit" disabled={!email.trim() || forgot.isPending} className="w-full bg-emerald-600 hover:bg-emerald-500 h-11 text-base">
                {forgot.isPending ? "در حال ارسال..." : "ارسال لینک بازیابی"}
              </Button>
            </div>
          </form>

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
