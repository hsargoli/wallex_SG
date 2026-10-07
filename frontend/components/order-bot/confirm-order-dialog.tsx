"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Loader2, ShieldAlert } from "lucide-react";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export type ConfirmPayload = {
  symbol: string;
  side: string;
  type: string;
  quantity: string | number;
  price?: string | number;
  stop_price?: string | number;
  stop_price_condition?: string;
};

const TYPE_LABEL: Record<string, string> = {
  LIMIT: "Limit",
  STOP_LIMIT: "Stop-Limit",
  MARKET: "Market",
  STOP_MARKET: "Stop-Market",
};

function Row({ k, v, cls }: { k: string; v: string; cls?: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1.5 text-sm">
      <span className="text-muted-foreground">{k}</span>
      <span dir="ltr" className={cn("font-mono font-semibold", cls)}>
        {v}
      </span>
    </div>
  );
}

export function ConfirmOrderDialog({
  payload,
  busy,
  onConfirm,
  onCancel,
}: {
  payload: ConfirmPayload | null;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const [ack, setAck] = useState(false);

  useEffect(() => {
    setAck(false);
  }, [payload]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) onCancel();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [busy, onCancel]);

  if (!payload || typeof document === "undefined") return null;

  const isBuy = payload.side === "BUY";
  const qty = Number(payload.quantity);
  const price = Number(payload.price ?? 0);
  const total = qty * price;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"
      onClick={() => !busy && onCancel()}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-md rounded-2xl border border-red-500/30 bg-background p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center gap-2 text-red-500">
          <ShieldAlert className="h-5 w-5" />
          <h2 className="text-base font-bold">تأیید ثبت سفارش واقعی</h2>
        </div>
        <p className="mb-3 text-xs text-muted-foreground">
          این سفارش با پول واقعی روی والکس ثبت می‌شود و تا اجرا یا لغو باقی می‌ماند.
        </p>

        <div className="divide-y divide-white/5 rounded-xl border border-white/10 px-3">
          <Row k="نماد" v={payload.symbol} />
          <Row k="سمت" v={isBuy ? "خرید" : "فروش"} cls={isBuy ? "text-emerald-500" : "text-red-500"} />
          <Row k="نوع" v={TYPE_LABEL[payload.type] ?? payload.type} />
          <Row k="مقدار" v={String(payload.quantity)} />
          {payload.price !== undefined && <Row k="قیمت" v={String(payload.price)} />}
          {payload.stop_price !== undefined && (
            <Row k="قیمت توقف" v={`${payload.stop_price_condition ?? ""} ${payload.stop_price}`} />
          )}
          <Row k="ارزش کل ≈" v={`${formatNumber(total)} TMN`} cls="text-amber-500" />
        </div>

        <label className="mt-4 flex cursor-pointer items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={ack}
            onChange={(e) => setAck(e.target.checked)}
            className="mt-1"
          />
          <span>متوجه‌ام که این یک سفارش واقعی است و مشخصات بالا را بررسی کرده‌ام.</span>
        </label>

        <div className="mt-5 flex gap-2">
          <button
            type="button"
            disabled={!ack || busy}
            onClick={onConfirm}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-white transition",
              isBuy ? "bg-emerald-600 hover:bg-emerald-700" : "bg-red-600 hover:bg-red-700",
              "disabled:cursor-not-allowed disabled:opacity-40",
            )}
          >
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            تأیید و ثبت سفارش {isBuy ? "خرید" : "فروش"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={onCancel}
            className="rounded-lg border border-white/10 px-4 py-2 text-sm hover:bg-white/5 disabled:opacity-40"
          >
            انصراف
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
