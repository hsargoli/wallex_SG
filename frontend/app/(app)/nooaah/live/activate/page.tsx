"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ChevronRight,
  ChevronLeft,
  Loader2,
  ShieldAlert,
  Wallet,
  Sliders,
  Layers,
  Target,
  X,
} from "lucide-react";
import {
  useNooaahConfig,
  useNooaahReadiness,
  useActivateNooaahLive,
  useNooaahLiveDraft,
  useUpdateNooaahLiveDraft,
  useClearNooaahLiveDraft,
} from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const CONFIRMATION_PHRASE = "با مسئولیت خودم";
const TOTAL_STEPS = 6;

type Draft = Record<string, unknown>;

const formatNum = (n: number) => n.toLocaleString("en-US");

function num(v: unknown, fallback: number = 0): number {
  const x = Number(v);
  return Number.isFinite(x) ? x : fallback;
}

function str(v: unknown, fallback: string = ""): string {
  return typeof v === "string" ? v : fallback;
}

export default function ActivateLivePage() {
  const cfg = useNooaahConfig();
  const readiness = useNooaahReadiness();
  const draftQ = useNooaahLiveDraft();
  const updateDraft = useUpdateNooaahLiveDraft();
  const clearDraft = useClearNooaahLiveDraft();
  const activate = useActivateNooaahLive();

  const [step, setStep] = useState(1);
  const [typed, setTyped] = useState("");

  // Local form state (sync از draft در هر load)
  const [form, setForm] = useState<Draft>({});
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (draftQ.data && !initialized) {
      // merge: defaults + draft
      setForm({ ...draftQ.data.defaults, ...draftQ.data.draft });
      setInitialized(true);
    }
  }, [draftQ.data, initialized]);

  const setField = (key: string, value: unknown) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const saveAndNext = async () => {
    // ذخیره‌ی کل form به عنوان draft (server merge می‌کنه)
    try {
      await updateDraft.mutateAsync(form);
      setStep((s) => Math.min(TOTAL_STEPS, s + 1));
    } catch {
      // خطا در save — از step رد نشو
    }
  };

  const goBack = () => setStep((s) => Math.max(1, s - 1));

  const reset = async () => {
    await clearDraft.mutateAsync();
    setForm(draftQ.data?.defaults ?? {});
    setStep(1);
    setTyped("");
    setInitialized(false);
  };

  const phraseOk = typed.trim() === CONFIRMATION_PHRASE;
  const canActivate =
    readiness.data?.all_met === true &&
    phraseOk &&
    !activate.isPending &&
    cfg.data?.mode === "paper-testing";

  const submitActivate = () => {
    if (!canActivate) return;
    activate.mutate(typed);
  };

  // بعد از activate
  if (cfg.data?.mode === "live-active") {
    return (
      <div className="mx-auto max-w-2xl p-6" dir="rtl">
        <Card className="border-emerald-500/40 bg-emerald-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-emerald-500">
              <CheckCircle2 className="h-5 w-5" />
              Live فعال شد
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">
              ربات در حالت Live فعاله. مرحله‌ی فعلی:{" "}
              <span className="font-bold">Stage {cfg.data.live_stage}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              برای ارتقا به Stage بعدی، ۵ معامله‌ی برنده‌ی live لازمه.
            </p>
            <Link
              href="/nooaah"
              className="inline-flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground"
            >
              بازگشت به داشبورد
              <ChevronRight className="h-4 w-4" />
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-red-500" />
          <h1 className="text-2xl font-bold">فعال‌سازی Live</h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={reset}
            className="text-xs text-muted-foreground hover:underline"
            disabled={clearDraft.isPending}
          >
            <X className="inline h-3 w-3" /> شروع دوباره
          </button>
          <Link href="/nooaah" className="text-sm text-muted-foreground hover:underline">
            بازگشت
          </Link>
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>مرحله {step} از {TOTAL_STEPS}</span>
          <span>{Math.round(((step - 1) / (TOTAL_STEPS - 1)) * 100)}٪</span>
        </div>
        <div className="flex gap-1">
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-all ${
                i < step ? "bg-emerald-500" : "bg-border"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Step content */}
      {step === 1 && <StepReview readiness={readiness.data} />}
      {step === 2 && <StepStrategy form={form} setField={setField} />}
      {step === 3 && <StepPosition form={form} setField={setField} />}
      {step === 4 && <StepCapital form={form} setField={setField} cfg={cfg.data} />}
      {step === 5 && <StepRisk form={form} setField={setField} />}
      {step === 6 && (
        <StepConfirm
          form={form}
          readinessMet={readiness.data?.all_met === true}
          typed={typed}
          setTyped={setTyped}
          phraseOk={phraseOk}
        />
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button
          variant="outline"
          onClick={goBack}
          disabled={step === 1 || updateDraft.isPending}
        >
          <ChevronRight className="h-4 w-4" />
          <span className="mr-2">قبلی</span>
        </Button>

        {step < TOTAL_STEPS ? (
          <Button
            onClick={saveAndNext}
            disabled={updateDraft.isPending}
            className="flex-1"
          >
            {updateDraft.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : null}
            <span className="mr-2">ذخیره و بعدی</span>
            <ChevronLeft className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            variant="destructive"
            onClick={submitActivate}
            disabled={!canActivate}
            className="flex-1"
          >
            {activate.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ShieldAlert className="h-4 w-4" />
            )}
            <span className="mr-2">
              {activate.isPending ? "در حال فعال‌سازی..." : "فعال‌سازی Live (پول واقعی)"}
            </span>
          </Button>
        )}
      </div>

      {activate.error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/5 p-3 text-sm text-red-500">
          خطا: {(activate.error as Error).message}
        </div>
      )}
    </div>
  );
}

// ============================================================
// Steps
// ============================================================

function StepReview({ readiness }: { readiness: any }) {
  return (
    <Card className="border-red-500/40 bg-red-500/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base text-red-500">
          <AlertTriangle className="h-4 w-4" />
          هشدار — پول واقعی
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <ul className="list-inside list-disc space-y-1 text-xs text-muted-foreground">
          <li>پس از فعال‌سازی، سفارش‌های ربات روی صرافی والکس ثبت می‌شوند.</li>
          <li>سرمایه‌ی اختصاص‌داده‌شده در معرض ریسک است.</li>
          <li>عمل فعال‌سازی برگشت‌ناپذیر است (فقط می‌توان متوقف کرد).</li>
          <li>مرحله‌ی اول: ۱۰٪ از سرمایه‌ی کل (Staged Rollout).</li>
        </ul>

        {readiness && (
          <>
            <div className="mt-4 border-t border-border/40 pt-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-bold">شرایط آماده‌سازی</span>
                <span className={readiness.all_met ? "text-emerald-500" : "text-amber-500"}>
                  {readiness.conditions.filter((c: any) => c.met).length} از{" "}
                  {readiness.conditions.length}
                </span>
              </div>
              <div className="space-y-1.5">
                {readiness.conditions.map((c: any) => (
                  <div
                    key={c.key}
                    className={`flex items-center justify-between gap-2 rounded border p-1.5 text-xs ${
                      c.met ? "border-emerald-500/30" : "border-red-500/30"
                    }`}
                  >
                    <span className="flex items-center gap-1.5">
                      {c.met ? (
                        <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <XCircle className="h-3 w-3 text-red-500" />
                      )}
                      <span className="truncate">{c.label}</span>
                    </span>
                    <span className="whitespace-nowrap font-mono text-[10px]" dir="ltr">
                      {c.current} / {c.target} {c.unit}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function StepStrategy({
  form,
  setField,
}: {
  form: Draft;
  setField: (k: string, v: unknown) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sliders className="h-4 w-4" />
          پارامترهای استراتژی
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <NumRow
          label="حداقل اطمینان (min_confidence)"
          value={num(form.min_confidence, 85)}
          onChange={(v) => setField("min_confidence", v)}
          min={0}
          max={100}
          step={1}
          hint="پیشنهاد: ۸۵ (محافظه‌کارانه)"
        />
        <NumRow
          label="تأیید متوالی (confirmation_candles)"
          value={num(form.confirmation_candles, 2)}
          onChange={(v) => setField("confirmation_candles", v)}
          min={1}
          max={5}
          step={1}
          hint="پیشنهاد: ۲"
        />
        <NumRow
          label="حد سود (tp_atr_mult)"
          value={num(form.tp_atr_mult, 3.0)}
          onChange={(v) => setField("tp_atr_mult", v)}
          min={1}
          max={10}
          step={0.5}
          hint="پیشنهاد: ۳.۰ (چند برابر ATR)"
        />
        <NumRow
          label="حد ضرر (sl_atr_mult)"
          value={num(form.sl_atr_mult, 1.5)}
          onChange={(v) => setField("sl_atr_mult", v)}
          min={0.5}
          max={5}
          step={0.1}
          hint="پیشنهاد: ۱.۵"
        />
        <NumRow
          label="فیلتر حجم (volume_z_min)"
          value={num(form.volume_z_min, -0.5)}
          onChange={(v) => setField("volume_z_min", v)}
          min={-5}
          max={2}
          step={0.1}
          hint="پیشنهاد: -۰.۵"
        />
      </CardContent>
    </Card>
  );
}

function StepPosition({
  form,
  setField,
}: {
  form: Draft;
  setField: (k: string, v: unknown) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Layers className="h-4 w-4" />
          مدیریت پوزیشن
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <NumRow
          label="حداکثر پوزیشن همزمان (max_concurrent_positions)"
          value={num(form.max_concurrent_positions, 1)}
          onChange={(v) => setField("max_concurrent_positions", v)}
          min={1}
          max={10}
          step={1}
          hint="پیشنهاد: ۱ (بهینه‌شده برای این ربات)"
        />
        <NumRow
          label="تعداد نماد برای تحلیل (top_n)"
          value={num(form.top_n, 5)}
          onChange={(v) => setField("top_n", v)}
          min={3}
          max={15}
          step={1}
          hint="پیشنهاد: ۵ پرحجم‌ترین نماد"
        />
      </CardContent>
    </Card>
  );
}

function StepCapital({
  form,
  setField,
  cfg,
}: {
  form: Draft;
  setField: (k: string, v: unknown) => void;
  cfg: any;
}) {
  const [display, setDisplay] = useState(
    String(num(form.capital_total, 0))
  );

  useEffect(() => {
    const n = num(form.capital_total, 0);
    setDisplay(n ? formatNum(n) : "");
  }, [form.capital_total]);

  const handleChange = (raw: string) => {
    const digits = raw.replace(/\D/g, "");
    if (!digits) {
      setDisplay("");
      setField("capital_total", 0);
      return;
    }
    const n = Number(digits);
    setDisplay(formatNum(n));
    setField("capital_total", n);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Wallet className="h-4 w-4" />
          سرمایه
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          سرمایه‌ی اختصاص‌داده‌شده (تومان)
          <input
            type="text"
            inputMode="numeric"
            dir="ltr"
            value={display}
            onChange={(e) => handleChange(e.target.value)}
            className="h-10 rounded-lg border border-border bg-background px-3 text-left font-mono text-sm"
            placeholder="مثلاً 1,000,000"
          />
          <span className="mt-1 text-[10px] text-muted-foreground">
            این مبلغ از کیف پول شما به ربات اختصاص داده می‌شود.
          </span>
        </label>

        {cfg && cfg.capital_available > 0 && (
          <div className="rounded-lg border border-border/40 bg-muted/30 p-2 text-xs">
            موجودی فعلی Nooaah:{" "}
            <span className="font-mono font-bold" dir="ltr">
              {formatNum(cfg.capital_available)}
            </span>{" "}
            تومان
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StepRisk({
  form,
  setField,
}: {
  form: Draft;
  setField: (k: string, v: unknown) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="h-4 w-4" />
          مدیریت ریسک
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <NumRow
          label="سقف ضرر روزانه (٪)"
          value={num(form.daily_loss_limit_pct, 2.0)}
          onChange={(v) => setField("daily_loss_limit_pct", v)}
          min={0.1}
          max={20}
          step={0.1}
          hint="توصیه‌ی ربات: ۲٪ (۲× حداکثر افت backtest)"
        />
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-2 text-[10px] text-muted-foreground">
          اگر ضرر امروز به این حد برسد، ربات تا فردا هیچ معامله‌ی جدیدی نمی‌کند.
        </div>
      </CardContent>
    </Card>
  );
}

function StepConfirm({
  form,
  readinessMet,
  typed,
  setTyped,
  phraseOk,
}: {
  form: Draft;
  readinessMet: boolean;
  typed: string;
  setTyped: (v: string) => void;
  phraseOk: boolean;
}) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">مرور نهایی</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Row label="min_confidence" value={String(num(form.min_confidence, 85))} />
            <Row label="confirmation" value={String(num(form.confirmation_candles, 2))} />
            <Row label="tp_atr" value={String(num(form.tp_atr_mult, 3.0))} />
            <Row label="sl_atr" value={String(num(form.sl_atr_mult, 1.5))} />
            <Row label="vol_z_min" value={String(num(form.volume_z_min, -0.5))} />
            <Row label="max_positions" value={String(num(form.max_concurrent_positions, 1))} />
            <Row label="top_n" value={String(num(form.top_n, 5))} />
            <Row
              label="capital"
              value={formatNum(num(form.capital_total, 0))}
            />
            <Row
              label="daily_loss_limit"
              value={`${num(form.daily_loss_limit_pct, 2.0)}٪`}
            />
          </div>
        </CardContent>
      </Card>

      {!readinessMet && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/5 p-3 text-xs text-amber-500">
          <AlertTriangle className="h-4 w-4" />
          شرایط آماده‌سازی هنوز کامل نیست — فعال‌سازی ممکن نیست.
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">تأیید نهایی</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            برای فعال‌سازی، عبارت زیر را دقیقاً تایپ کن:
          </p>
          <div className="rounded-lg border border-border bg-muted/30 p-3 text-center text-sm font-bold">
            {CONFIRMATION_PHRASE}
          </div>
          <input
            type="text"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            placeholder="اینجا تایپ کن..."
            className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
          />
          {typed.length > 0 && !phraseOk && (
            <p className="text-xs text-red-500">عبارت مطابقت ندارد</p>
          )}
          {phraseOk && (
            <p className="text-xs text-emerald-500">✅ عبارت مطابقت دارد</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================
// Helpers
// ============================================================

function NumRow({
  label,
  value,
  onChange,
  min,
  max,
  step,
  hint,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  hint?: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted-foreground">
      <div className="flex items-center justify-between">
        <span className="font-mono">{label}</span>
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          dir="ltr"
          className="h-8 w-24 rounded-lg border border-border bg-background px-2 text-left font-mono text-sm"
        />
      </div>
      {hint && <span className="text-[10px] text-muted-foreground/70">{hint}</span>}
    </label>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded border border-border/40 p-2">
      <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
      <span className="font-mono font-bold" dir="ltr">
        {value}
      </span>
    </div>
  );
}
