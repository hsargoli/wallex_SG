"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Shield, AlertTriangle, ExternalLink, Key, Loader2 } from "lucide-react";
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
  useConnectTradeWallex,
  useDisconnectTradeWallex,
} from "@/lib/queries";
import { toast } from "sonner";
import { extractErrorMessage } from "@/lib/api";

function formatDate(d: string | null | undefined) {
  if (!d) return "—";
  try { return new Date(d).toLocaleString("fa-IR"); } catch { return "—"; }
}

export default function WallexSettingsPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [tradeToken, setTradeToken] = useState("");
  const [showTradeToken, setShowTradeToken] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!getUserToken()) router.replace("/login");
  }, [router]);

  const { data, isLoading, error } = useWallexStatus();
  const connectMut = useConnectWallex();
  const disconnectMut = useDisconnectWallex();
  const connectTradeMut = useConnectTradeWallex();
  const disconnectTradeMut = useDisconnectTradeWallex();

  if (!mounted) return null;

  const isViewConnected = data?.view_connected ?? false;
  const hasBalances = !!data?.balances && data.balances.length > 0;
  const revokeError = data?.error === "token_revoked";
  const decryptError = data?.error === "decrypt_failed";
  const unavailable = data?.error === "wallex_unavailable";

  const handleConnect = () => {
    if (!token.trim()) return;
    connectMut.mutate(token.trim(), { onSuccess: () => setToken("") });
  };

  const handleDisconnect = () => {
    if (confirm("اتصال به والکس قطع بشه؟")) disconnectMut.mutate();
  };

  const handleConnectTrade = () => {
    if (!tradeToken.trim()) return;
    connectTradeMut.mutate(tradeToken.trim(), {
      onSuccess: () => { setTradeToken(""); toast.success("توکن معاملات ذخیره شد."); },
      onError: (err: unknown) => toast.error(extractErrorMessage(err)),
    });
  };

  const handleDisconnectTrade = () => {
    if (confirm("اتصال توکن معاملات قطع بشه؟")) {
      disconnectTradeMut.mutate(undefined, {
        onSuccess: () => toast.success("اتصال توکن معاملات قطع شد."),
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-1 text-xs text-muted-foreground">
            <Link href="/dashboard" className="hover:underline">داشبورد</Link> / تنظیمات
          </div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Key className="h-6 w-6 text-amber-400" /> اتصال به والکس
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            برای دیدن دارایی و انجام معامله، یکی از توکن‌های View یا Trade حساب والکس را وارد کنید.
          </p>
        </div>
        <Button asChild variant="ghost" className="gap-2">
          <Link href="/dashboard"><ArrowLeft className="h-4 w-4" /> بازگشت</Link>
        </Button>
      </div>

      {isLoading && <Card><CardContent className="py-8"><Skeleton className="h-32 w-full" /></CardContent></Card>}
      {error && <Card className="border-amber-500/30 bg-amber-500/5"><CardContent className="flex items-center gap-3 py-4 text-sm"><AlertTriangle className="h-5 w-5 text-amber-400" /> خطا در دریافت وضعیت. لطفاً صفحه رو refresh کن.</CardContent></Card>}

      {/* View Token */}
      {!isLoading && !isViewConnected && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><Key className="h-5 w-5 text-violet-400" /> توکن View (اختیاری)</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-xs">
              <div className="flex items-center gap-2 font-semibold text-emerald-300"><Shield className="h-4 w-4" /> امنیت</div>
              <p className="mt-1 text-muted-foreground">اگر توکن Trade را وارد کنید، نیازی به این توکن نیست. در غیر این صورت می‌توانید از این توکن برای خواندن استفاده کنید.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="token">توکن View والکس</Label>
              <div className="flex gap-2">
                <Input id="token" type={showToken ? "text" : "password"} value={token} onChange={(e) => setToken(e.target.value)} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" dir="ltr" className="font-mono text-xs" />
                <Button type="button" variant="outline" onClick={() => setShowToken(s => !s)} className="shrink-0">{showToken ? "پنهان" : "نمایش"}</Button>
              </div>
            </div>
            <Button onClick={handleConnect} disabled={!token.trim() || connectMut.isPending} className="w-full gap-2 bg-violet-600 hover:bg-violet-500">
              {connectMut.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> در حال تماس با والکس...</> : "اتصال و اعتبارسنجی"}
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && isViewConnected && (
        <>
          <Card className="border-emerald-500/30 bg-emerald-500/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 py-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
                <div><p className="font-semibold text-emerald-300">متصل به والکس</p><p className="text-xs text-muted-foreground">از {formatDate(data?.connected_at)}</p></div>
              </div>
              <Button onClick={handleDisconnect} disabled={disconnectMut.isPending} variant="outline" className="border-rose-500/40 text-rose-300 hover:bg-rose-500/10">{disconnectMut.isPending ? "..." : "قطع اتصال"}</Button>
            </CardContent>
          </Card>
          
          {revokeError && <Card className="border-amber-500/30 bg-amber-500/5"><CardContent className="flex items-center gap-3 py-3 text-sm"><AlertTriangle className="h-5 w-5 text-amber-400" /> توکن در والکس revoke شده.</CardContent></Card>}
          {decryptError && <Card className="border-rose-500/30 bg-rose-500/5"><CardContent className="flex items-center gap-3 py-3 text-sm"><AlertTriangle className="h-5 w-5 text-rose-400" /> توکن ذخیره‌شده قابل رمزگشایی نیست.</CardContent></Card>}
          {unavailable && <Card className="border-amber-500/30 bg-amber-500/5"><CardContent className="flex items-center gap-3 py-3 text-sm"><AlertTriangle className="h-5 w-5 text-amber-400" /> الان نمی‌تونیم به والکس وصل شیم.</CardContent></Card>}

          {hasBalances && (
            <Card>
              <CardHeader><CardTitle className="text-lg">دارایی‌های واقعی والکس</CardTitle></CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-lg border border-white/10">
                  <table className="w-full text-sm"><thead className="bg-white/5 text-xs text-muted-foreground"><tr><th className="px-3 py-2 text-right">دارایی</th><th className="px-3 py-2 text-left">موجود</th><th className="px-3 py-2 text-left">قفل‌شده</th><th className="px-3 py-2 text-left">کل</th></tr></thead>
                    <tbody>{data!.balances!.map((b) => (
                      <tr key={b.asset} className="border-t border-white/5 hover:bg-white/5">
                        <td className="px-3 py-2 font-mono" dir="ltr"><Badge variant="outline">{b.asset}</Badge></td>
                        <td className="px-3 py-2 text-left font-mono text-xs" dir="ltr">{Number(b.available).toLocaleString("en-US", { maximumFractionDigits: 8 })}</td>
                        <td className="px-3 py-2 text-left font-mono text-xs text-muted-foreground" dir="ltr">{Number(b.locked).toLocaleString("en-US", { maximumFractionDigits: 8 })}</td>
                        <td className="px-3 py-2 text-left font-mono text-xs" dir="ltr">{Number(b.total).toLocaleString("en-US", { maximumFractionDigits: 8 })}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Trade Token Section (Exactly like View) */}
      <Card className={`mt-8 ${data?.trade_connected ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-emerald-500/20'}`}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><Shield className={`h-5 w-5 ${data?.trade_connected ? 'text-emerald-400' : 'text-emerald-500'}`} /> توکن معاملات (Trade Token)</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {data?.trade_connected ? (
            <div className="flex flex-wrap items-center justify-between gap-4 py-2">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
                <div><p className="font-semibold text-emerald-300">توکن معاملات متصل است</p><p className="text-xs text-muted-foreground">از {formatDate(data?.trade_connected_at)}</p></div>
              </div>
              <Button onClick={handleDisconnectTrade} disabled={disconnectTradeMut.isPending} variant="outline" className="border-rose-500/40 text-rose-300 hover:bg-rose-500/10">{disconnectTradeMut.isPending ? "..." : "قطع اتصال"}</Button>
            </div>
          ) : (
            <>
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-xs mb-4">
                <div className="flex items-center gap-2 font-semibold text-emerald-300"><Shield className="h-4 w-4" /> امنیت</div>
                <p className="mt-1 text-muted-foreground">توکن معاملات شما با AES رمزنگاری می‌شه و فقط برای ثبت سفارش استفاده می‌شه.</p>
              </div>
              <div className="space-y-2">
                <Label>توکن Trade والکس</Label>
                <div className="flex gap-2">
                  <Input type={showTradeToken ? "text" : "password"} value={tradeToken} onChange={(e) => setTradeToken(e.target.value)} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" dir="ltr" className="font-mono text-xs" />
                  <Button type="button" variant="outline" onClick={() => setShowTradeToken(s => !s)} className="shrink-0">{showTradeToken ? "پنهان" : "نمایش"}</Button>
                </div>
              </div>
              <Button onClick={handleConnectTrade} disabled={!tradeToken.trim() || connectTradeMut.isPending} className="w-full gap-2 bg-emerald-600 hover:bg-emerald-500">
                {connectTradeMut.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> در حال تماس با والکس...</> : "ذخیره توکن معاملات"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
