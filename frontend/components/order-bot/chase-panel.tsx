"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Crosshair, Loader2, Square } from "lucide-react";
import { chaseApi, type ChaseCreate } from "@/lib/api";
import { useOrderBook } from "@/lib/queries";
import { useLiveMode } from "@/lib/hooks/use-live-mode";
import { formatClock } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { ConfirmOrderDialog, type ConfirmPayload } from "./confirm-order-dialog";

const STATUS_FA: Record<string, string> = {
  running: "در حال اجرا",
  done: "کامل شد",
  stopped: "متوقف",
  expired: "مهلت تمام شد",
  error: "خطا",
  limit: "سقف جابه‌جایی",
};

export function ChasePanel() {
  const qc = useQueryClient();
  const { liveOn } = useLiveMode();
  const [open, setOpen] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [low, setLow] = useState("");
  const [high, setHigh] = useState("");
  const [qty, setQty] = useState("");
  const [maxNotional, setMaxNotional] = useState("");
  const [dry, setDry] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<ConfirmPayload | null>(null);

  const sym = symbol.trim().toUpperCase();
  const book = useOrderBook(sym.length >= 5 ? sym : null);
  const list = useQuery({
    queryKey: ["chase-list"],
    queryFn: chaseApi.list,
    refetchInterval: 5000,
    enabled: open,
  });

  const create = useMutation({
    mutationFn: (b: ChaseCreate) => chaseApi.create(b),
    onSuccess: () => {
      setConfirm(null);
      setErr(null);
      qc.invalidateQueries({ queryKey: ["chase-list"] });
    },
    onError: (e: any) => {
      setConfirm(null);
      const d = e?.response?.data?.detail;
      setErr(typeof d === "string" ? d : d ? JSON.stringify(d) : (e?.message ?? "خطا"));
    },
  });
  const stop = useMutation({
    mutationFn: (id: string) => chaseApi.stop(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chase-list"] }),
  });

  const body = (): ChaseCreate => ({
    symbol: sym,
    side,
    low,
    high,
    quantity: qty,
    dry_run: dry,
    max_notional: maxNotional ? maxNotional : null,
  });

  const submit = () => {
    setErr(null);
    const l = Number(low), h = Number(high), q = Number(qty);
    if (sym.length < 5) return setErr("نماد را وارد کن (مثلاً PEPETMN)");
    if (!(l > 0 && h > 0 && q > 0)) return setErr("کف، سقف و مقدار باید بزرگ‌تر از صفر باشند");
    if (l > h) return setErr("کف نباید از سقف بزرگ‌تر باشد");
    if (dry) return create.mutate(body());
    if (!liveOn) return setErr("معامله واقعی غیرفعال است");
    if (!(Number(maxNotional) > 0)) return setErr("در حالت واقعی سقف ارزش کل الزامی است");
    setConfirm({
      symbol: sym,
      side,
      type: "تعقیب بهترین قیمت",
      quantity: qty,
      price: side === "BUY" ? high : low,
    });
  };

  return (
    <Card className="border-violet-500/20">
      <CardHeader className="cursor-pointer pb-3" onClick={() => setOpen((v) => !v)}>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Crosshair className="h-5 w-5 text-violet-400" />
            تعقیب بهترین قیمت
            <Badge variant="outline" className="text-[10px]">پیش‌فرض: شبیه‌سازی</Badge>
          </span>
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </CardTitle>
      </CardHeader>
      {open && (
        <CardContent className="space-y-4">
          <p className="text-xs text-muted-foreground">
            وقتی قیمت در بازه است، سفارش Limit را هر ۶۰ ثانیه در صدر دفتر نگه می‌دارد
            (یک tick بالاتر از بهترین خریدار برای خرید، یک tick پایین‌تر از بهترین فروشنده برای فروش) و هرگز بیرون بازه نمی‌رود.
          </p>

          <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
            <Input dir="ltr" placeholder="نماد، مثل PEPETMN" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
            <div className="flex gap-2">
              {(["BUY", "SELL"] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSide(s)}
                  className={cn(
                    "flex-1 rounded-lg border px-3 py-2 text-sm",
                    side === s
                      ? s === "BUY" ? "border-emerald-500 bg-emerald-500/15 text-emerald-500" : "border-red-500 bg-red-500/15 text-red-500"
                      : "border-white/10 text-muted-foreground",
                  )}
                >
                  {s === "BUY" ? "خرید" : "فروش"}
                </button>
              ))}
            </div>
            <Input dir="ltr" placeholder="مقدار" value={qty} onChange={(e) => setQty(e.target.value)} />
            <Input dir="ltr" placeholder={side === "BUY" ? "کف بازه" : "کف بازه (حداقل فروش)"} value={low} onChange={(e) => setLow(e.target.value)} />
            <Input dir="ltr" placeholder={side === "BUY" ? "سقف بازه (حداکثر خرید)" : "سقف بازه"} value={high} onChange={(e) => setHigh(e.target.value)} />
            <Input dir="ltr" placeholder="سقف ارزش کل (TMN) — برای واقعی الزامی" value={maxNotional} onChange={(e) => setMaxNotional(e.target.value)} />
          </div>

          {book.data && (
            <div className="flex flex-wrap gap-4 rounded-lg border border-white/10 p-2 text-xs" dir="ltr">
              <span>best bid: <b className="font-mono text-emerald-500">{book.data.best_bid ?? "—"}</b></span>
              <span>best ask: <b className="font-mono text-red-500">{book.data.best_ask ?? "—"}</b></span>
              <span>spread: <b className="font-mono">{book.data.spread ?? "—"}</b></span>
            </div>
          )}

          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input type="checkbox" checked={dry} onChange={(e) => setDry(e.target.checked)} />
            حالت شبیه‌سازی (فقط لاگ، بدون ثبت سفارش)
          </label>
          {!dry && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-xs text-red-600 dark:text-red-400">
              حالت واقعی: ربات با پول واقعی سفارش می‌گذارد، لغو می‌کند و دوباره می‌گذارد.
            </p>
          )}

          {err && <p className="text-xs text-red-500">{err}</p>}

          <button
            type="button"
            onClick={submit}
            disabled={create.isPending || (!dry && !liveOn)}
            className="flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-40"
          >
            {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {dry ? "شروع شبیه‌سازی" : "شروع تعقیب واقعی"}
          </button>

          <div className="space-y-3 border-t border-white/10 pt-3">
            {(list.data?.items ?? []).length === 0 && (
              <p className="text-xs text-muted-foreground">تعقیبی ثبت نشده</p>
            )}
            {(list.data?.items ?? []).map((c) => (
              <div key={c.id} className="rounded-xl border border-white/10 p-3 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm font-bold">{c.symbol}</span>
                  <Badge variant="outline" className={c.side === "BUY" ? "text-emerald-500" : "text-red-500"}>
                    {c.side === "BUY" ? "خرید" : "فروش"}
                  </Badge>
                  <Badge variant="outline">{STATUS_FA[c.status] ?? c.status}</Badge>
                  {c.dry_run && <Badge variant="outline" className="text-amber-500">شبیه‌سازی</Badge>}
                  {c.status === "running" && (
                    <button
                      type="button"
                      onClick={() => stop.mutate(c.id)}
                      disabled={stop.isPending}
                      className="mr-auto flex items-center gap-1 rounded-md border border-red-500/40 px-2 py-1 text-red-500 hover:bg-red-500/10"
                    >
                      <Square className="h-3 w-3" />
                      توقف و لغو سفارش
                    </button>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground" dir="ltr">
                  <span>range {c.low} – {c.high}</span>
                  <span>qty {c.quantity}</span>
                  <span>filled {c.filled}</span>
                  <span>moves {c.moves}</span>
                  <span>own {c.own_price ?? "—"}</span>
                </div>
                {c.last_reason && <p className="mt-1">آخرین تصمیم: {c.last_action} — {c.last_reason}</p>}
                <div className="mt-2 max-h-32 overflow-auto rounded-md bg-black/20 p-2 font-mono text-[10px] leading-5" dir="ltr">
                  {[...c.log].reverse().slice(0, 12).map((l, i) => (
                    <div key={i}>{formatClock(l.t)} {l.msg}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      )}
      <ConfirmOrderDialog
        payload={confirm}
        busy={create.isPending}
        onConfirm={() => create.mutate(body())}
        onCancel={() => setConfirm(null)}
      />
    </Card>
  );
}
