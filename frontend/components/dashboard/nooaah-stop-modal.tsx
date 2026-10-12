"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Loader2,
  Banknote,
  Pause,
  ShieldOff,
  X,
} from "lucide-react";
import {
  useNooaahStopPreview,
  useStopNooaahLive,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";

type StopAction = "sell" | "pause" | "kill";

interface Props {
  open: boolean;
  onClose: () => void;
  onDone: () => void;
}

const pnlColor = (v: number) =>
  v > 0 ? "text-emerald-500" : v < 0 ? "text-red-500" : "text-muted-foreground";

const fmt = (n: number) => n.toLocaleString("en-US");

export function NooaahStopModal({ open, onClose, onDone }: Props) {
  const preview = useNooaahStopPreview(open);
  const stop = useStopNooaahLive();

  const [confirming, setConfirming] = useState<StopAction | null>(null);

  if (!open) return null;

  const doStop = (action: StopAction) => {
    stop.mutate(action, {
      onSuccess: () => {
        setConfirming(null);
        onDone();
      },
    });
  };

  const count = preview.data?.count ?? 0;
  const noPositions = count === 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" dir="rtl">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-5 shadow-2xl">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-bold">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            توقف ربات
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted"
            disabled={stop.isPending}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Loading */}
        {preview.isLoading && (
          <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            در حال دریافت وضعیت پوزیشن‌ها...
          </div>
        )}

        {/* Preview + Options */}
        {preview.data && !confirming && (
          <>
            {noPositions ? (
              <div className="rounded-lg border border-border/50 bg-muted/30 p-3 text-sm">
                هیچ پوزیشن بازی وجود ندارد. ربات به‌سادگی متوقف می‌شود.
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground">
                  {count} پوزیشن باز — کل سود/ضرر:{" "}
                  <span className={pnlColor(preview.data.total_pnl_abs)}>
                    {fmt(preview.data.total_pnl_abs)} تومان
                  </span>
                </div>

                <div className="max-h-48 space-y-1 overflow-y-auto rounded-lg border border-border/40">
                  {preview.data.open_positions.map((p: import("@/lib/api").NooaahStopPosition) => (
                    <div
                      key={p.client_id}
                      className="flex items-center justify-between gap-2 border-b border-border/40 p-2 text-xs last:border-0"
                    >
                      <span className="font-mono font-bold">{p.symbol}</span>
                      <span className="font-mono text-muted-foreground" dir="ltr">
                        {fmt(p.entry_price)} → {fmt(p.best_bid)}
                      </span>
                      <span className={`font-mono font-bold ${pnlColor(p.pnl_pct)}`} dir="ltr">
                        {p.pnl_pct >= 0 ? "+" : ""}
                        {p.pnl_pct.toFixed(2)}٪
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="mt-4 space-y-2">
              <ActionRow
                icon={<Banknote className="h-4 w-4" />}
                title="فروش با قیمت بازار"
                desc="همه‌ی پوزیشن‌ها با بهترین قیمت خریدار فروخته می‌شن و پول برمی‌گرده"
                onClick={() => {
                  if (noPositions) doStop("pause");
                  else setConfirming("sell");
                }}
                disabled={stop.isPending}
                color="primary"
              />
              <ActionRow
                icon={<Pause className="h-4 w-4" />}
                title="توقف موقت"
                desc="پوزیشن‌ها باز می‌مونن، ربات متوقف می‌شه — قابل ادامه دادن"
                onClick={() => doStop("pause")}
                disabled={stop.isPending}
                color="default"
              />
              <ActionRow
                icon={<ShieldOff className="h-4 w-4" />}
                title="توقف کامل (Kill)"
                desc="پوزیشن‌ها باز می‌مونن ولی ربات دیگه روشن نمی‌شه — نیاز به reset"
                onClick={() => setConfirming("kill")}
                disabled={stop.isPending}
                color="destructive"
              />
            </div>
          </>
        )}

        {/* Confirmation for sell */}
        {confirming === "sell" && (
          <ConfirmBlock
            title="فروش همه‌ی پوزیشن‌ها"
            description={`همه‌ی ${count} پوزیشن با بهترین قیمت خریدار فروخته می‌شن. این عمل قابل برگشت نیست.`}
            actionLabel="تأیید فروش"
            onCancel={() => setConfirming(null)}
            onConfirm={() => doStop("sell")}
            isPending={stop.isPending}
            variant="default"
          />
        )}

        {/* Confirmation for kill */}
        {confirming === "kill" && (
          <ConfirmBlock
            title="توقف کامل (Kill-Switch)"
            description="پوزیشن‌ها باز می‌مونن. ربات دیگه روشن نمی‌شه — برای برگشت به حالت عادی نیاز به reset کامل state هست. این عمل برگشت‌ناپذیره."
            actionLabel="بله، Kill کن"
            onCancel={() => setConfirming(null)}
            onConfirm={() => doStop("kill")}
            isPending={stop.isPending}
            variant="destructive"
          />
        )}

        {stop.error && (
          <div className="mt-3 rounded-lg border border-red-500/40 bg-red-500/5 p-2 text-xs text-red-500">
            خطا: {(stop.error as Error).message}
          </div>
        )}
      </div>
    </div>
  );
}

function ActionRow({
  icon,
  title,
  desc,
  onClick,
  disabled,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
  onClick: () => void;
  disabled: boolean;
  color: "primary" | "default" | "destructive";
}) {
  const cls =
    color === "destructive"
      ? "border-red-500/40 hover:bg-red-500/5"
      : color === "primary"
      ? "border-emerald-500/40 hover:bg-emerald-500/5"
      : "border-border/50 hover:bg-muted/50";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex w-full items-start gap-3 rounded-lg border p-3 text-right transition-all disabled:opacity-50 ${cls}`}
    >
      <span className="mt-0.5 shrink-0">{icon}</span>
      <span className="flex-1">
        <span className="block text-sm font-bold">{title}</span>
        <span className="mt-0.5 block text-xs text-muted-foreground">{desc}</span>
      </span>
    </button>
  );
}

function ConfirmBlock({
  title,
  description,
  actionLabel,
  onCancel,
  onConfirm,
  isPending,
  variant,
}: {
  title: string;
  description: string;
  actionLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
  isPending: boolean;
  variant: "default" | "destructive";
}) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-amber-500/40 bg-amber-500/5 p-3">
        <div className="text-sm font-bold">{title}</div>
        <div className="mt-1 text-xs text-muted-foreground">{description}</div>
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={onCancel}
          disabled={isPending}
          className="flex-1"
        >
          انصراف
        </Button>
        <Button
          variant={variant === "destructive" ? "destructive" : "default"}
          onClick={onConfirm}
          disabled={isPending}
          className="flex-1"
        >
          {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          <span className="mr-2">{actionLabel}</span>
        </Button>
      </div>
    </div>
  );
}
