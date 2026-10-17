"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Shield, AlertTriangle, ExternalLink, Key } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { getUserToken } from "@/lib/auth";
import {
  useWallexStatus,
  useConnectWallex,
  useDisconnectWallex,
} from "@/lib/queries";

export default function WallexSettingsPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    setMounted(true);
    // auth guard
    if (!getUserToken()) {
      router.replace("/login");
    }
  }, [router]);

  const { data, isLoading, error } = useWallexStatus();
  const connectMut = useConnectWallex();
  const disconnectMut = useDisconnectWallex();

  if (!mounted) return null;

  const isConnected = data?.connected ?? false;
  const hasBalances = !!data?.balances && data.balances.length > 0;
  const revokeError = data?.error === "token_revoked";
  const decryptError = data?.error === "decrypt_failed";
  const unavailable = data?.error === "wallex_unavailable";

  const handleConnect = () => {
    if (!token.trim()) return;
    connectMut.mutate(token.trim(), {
      onSuccess: () => setToken(""),
    });
  };

  const handleDisconnect = () => {
    if (confirm("اتصال به والکس قطع بشه؟ تاریخچه‌ی معاملات حفظ می‌شه.")) {
      disconnectMut.mutate();
    }
  };

  return (
    <div className="space-y-6">
      {/* header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-1 text-xs text-muted-foreground">
            <Link href="/dashboard" className="hover:underline">داشبورد</Link>
            {" / "}
            تنظیمات
          </div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Key className="h-6 w-6 text-amber-400" />
            اتصال به والکس
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            برای دیدن دارایی واقعی خودت، توکن View حساب والکس رو وارد کن.
          </p>
        </div>
        <Button asChild variant="ghost" className="gap-2">
          <Link href="/dashboard">
            <ArrowLeft className="h-4 w-4" />
            بازگشت
          </Link>
        </Button>
      </div>

      {/* Loading */}
      {isLoading && (
        <Card>
          <CardContent className="py-8">
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      )}

      {/* Error fetch */}
      {error && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-center gap-3 py-4 text-sm">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            خطا در دریافت وضعیت. لطفاً صفحه رو refresh کن.
          </CardContent>
        </Card>
      )}

      {/* Disconnected */}
      {!isLoading && !isConnected && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Key className="h-5 w-5 text-violet-400" />
              توکن View خودتو وارد کن
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-xs">
              <div className="flex items-center gap-2 font-semibold text-emerald-300">
                <Shield className="h-4 w-4" />
                امنیت
              </div>
              <p className="mt-1 text-muted-foreground">
                توکن شما با AES رمزنگاری می‌شه و فقط برای خواندن (View) استفاده می‌شه. هرگز به frontend برنمی‌گرده.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="token">توکن View والکس</Label>
              <div className="flex gap-2">
                <Input
                  id="token"
                  type={showToken ? "text" : "password"}
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  dir="ltr"
                  className="font-mono text-xs"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowToken((s) => !s)}
                  className="shrink-0"
                >
                  {showToken ? "پنهان" : "نمایش"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                توکن رو از{" "}
                <a
                  href="https://wallex.ir/app/settings/api-management"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-violet-300 hover:underline"
                >
                  پنل والکس → مدیریت API
                  <ExternalLink className="h-3 w-3" />
                </a>{" "}
                بساز و اینجا وارد کن.
              </p>
            </div>

            <Button
              onClick={handleConnect}
              disabled={!token.trim() || connectMut.isPending}
              className="w-full gap-2 bg-violet-600 hover:bg-violet-500"
            >
              {connectMut.isPending ? "در حال اعتبارسنجی..." : "اتصال و اعتبارسنجی"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Connected */}
      {!isLoading && isConnected && (
        <>
          <Card className="border-emerald-500/30 bg-emerald-500/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
                <div>
                  <p className="font-semibold text-emerald-300">متصل به والکس</p>
                  <p className="text-xs text-muted-foreground">
                    از{" "}
                    {data?.connected_at
                      ? new Date(data.connected_at).toLocaleString("fa-IR")
                      : "—"}
                  </p>
                </div>
              </div>
              <Button
                onClick={handleDisconnect}
                disabled={disconnectMut.isPending}
                variant="outline"
                className="border-rose-500/40 text-rose-300 hover:bg-rose-500/10"
              >
                {disconnectMut.isPending ? "..." : "قطع اتصال"}
              </Button>
            </CardContent>
          </Card>

          {/* Errors */}
          {revokeError && (
            <Card className="border-amber-500/30 bg-amber-500/5">
              <CardContent className="flex items-center gap-3 py-3 text-sm">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
                توکن در والکس revoke شده. برای ادامه، دوباره متصل شو (اول قطع، بعد وصل).
              </CardContent>
            </Card>
          )}
          {decryptError && (
            <Card className="border-rose-500/30 bg-rose-500/5">
              <CardContent className="flex items-center gap-3 py-3 text-sm">
                <AlertTriangle className="h-5 w-5 text-rose-400" />
                توکن ذخیره‌شده قابل رمزگشایی نیست (کلید سرور عوض شده). لطفاً دوباره متصل شو.
              </CardContent>
            </Card>
          )}
          {unavailable && (
            <Card className="border-amber-500/30 bg-amber-500/5">
              <CardContent className="flex items-center gap-3 py-3 text-sm">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
                الان نمی‌تونیم به والکس وصل شیم. بعداً امتحان کن.
              </CardContent>
            </Card>
          )}

          {/* Balances */}
          {hasBalances && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">دارایی‌های واقعی والکس</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-lg border border-white/10">
                  <table className="w-full text-sm">
                    <thead className="bg-white/5 text-xs text-muted-foreground">
                      <tr>
                        <th className="px-3 py-2 text-right">دارایی</th>
                        <th className="px-3 py-2 text-left">موجود</th>
                        <th className="px-3 py-2 text-left">قفل‌شده</th>
                        <th className="px-3 py-2 text-left">کل</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data!.balances!.map((b) => (
                        <tr
                          key={b.asset}
                          className="border-t border-white/5 hover:bg-white/5"
                        >
                          <td className="px-3 py-2 font-mono" dir="ltr">
                            <Badge variant="outline">{b.asset}</Badge>
                          </td>
                          <td className="px-3 py-2 text-left font-mono text-xs" dir="ltr">
                            {Number(b.available).toLocaleString("en-US", {
                              maximumFractionDigits: 8,
                            })}
                          </td>
                          <td className="px-3 py-2 text-left font-mono text-xs text-muted-foreground" dir="ltr">
                            {Number(b.locked).toLocaleString("en-US", {
                              maximumFractionDigits: 8,
                            })}
                          </td>
                          <td className="px-3 py-2 text-left font-mono text-xs" dir="ltr">
                            {Number(b.total).toLocaleString("en-US", {
                              maximumFractionDigits: 8,
                            })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">
                  ⓘ Paper Trading از این دارایی‌ها مستقل است — با ۳ میلیون مجازی بازی می‌کنه.
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
