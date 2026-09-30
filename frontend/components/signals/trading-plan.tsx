"use client";

import { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  HelpCircle,
  ChevronDown,
  Target,
  Shield,
  Crosshair,
  ArrowRight,
} from "lucide-react";
import { type LevelsResponse } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// ==================== Guide ====================

export function LevelsGuide() {
  const [open, setOpen] = useState(false);
  return (
    <Card className="border-blue-500/20 bg-blue-500/5">
      <CardHeader
        className="flex cursor-pointer flex-row items-center justify-between space-y-0 py-3"
        onClick={() => setOpen((v) => !v)}
      >
        <CardTitle className="flex items-center gap-2 text-base">
          <HelpCircle className="h-5 w-5 text-blue-400" />
          راهنما: چطور از این سطوح استفاده کنم؟
        </CardTitle>
        <ChevronDown
          className={cn("h-4 w-4 transition", !open && "-rotate-90")}
        />
      </CardHeader>
      {open && (
        <CardContent className="space-y-4 pt-2 text-sm">
          <div>
            <p className="mb-2 font-semibold text-blue-300">
              📐 Pivot Points (نقاط چرخش)
            </p>
            <p className="text-muted-foreground">
              فرمول ریاضی که از High/Low/Close قبلی حساب می‌شه. ۷ سطح می‌ده:
              <span className="mx-1 font-mono text-red-400">R3,R2,R1</span> (سقف)
              — <span className="font-mono text-amber-400">PP</span> (مرکز) —
              <span className="mx-1 font-mono text-emerald-400">S1,S2,S3</span> (کف)
            </p>
          </div>
          <div>
            <p className="mb-2 font-semibold text-blue-300">
              🎯 Support/Resistance (حمایت/مقاومت)
            </p>
            <p className="text-muted-foreground">
              از تاریخ پیدا می‌شن. هر سطحی که قیمت چند بار بهش خورده و برگشته:
            </p>
            <ul className="mt-1 ml-4 list-disc space-y-0.5 text-muted-foreground">
              <li>
                <span className="text-emerald-400">🟢 ۵+ بار</span> = قوی (احتمال بالا)
              </li>
              <li>
                <span className="text-amber-400">🟡 ۳-۴ بار</span> = متوسط
              </li>
              <li>
                <span className="text-zinc-400">⚪ ۱-۲ بار</span> = ضعیف
              </li>
            </ul>
          </div>
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
            <p className="font-semibold text-blue-300">💡 قاعده‌ی طلایی</p>
            <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
              <li>قیمت <b>بالای PP</b> = تمایل به خرید</li>
              <li>قیمت <b>زیر PP</b> = تمایل به فروش</li>
              <li>رسیدن به <b>R1</b> = احتمال برگشت به پایین</li>
              <li>رسیدن به <b>S1</b> = احتمال برگشت به بالا</li>
            </ul>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// ==================== Trading Plan ====================

interface PlanLine {
  label: string;
  price: string;
  color: string;
  icon?: React.ElementType;
}

export function TradingPlan({ data }: { data: LevelsResponse }) {
  const current = Number(data.current_price);
  const pp = data.pivot ? Number(data.pivot.pp) : null;
  const r1 = data.pivot ? Number(data.pivot.r1) : null;
  const s1 = data.pivot ? Number(data.pivot.s1) : null;

  // قوی‌ترین سطوح
  const strongSupports = data.swings
    .filter((s) => s.type === "support")
    .filter((s) => Number(s.price) < current)
    .sort((a, b) => Number(b.price) - Number(a.price));

  const strongResistances = data.swings
    .filter((s) => s.type === "resistance")
    .filter((s) => Number(s.price) > current)
    .sort((a, b) => Number(a.price) - Number(b.price));

  const nearestSupport = strongSupports[0];
  const nearestResistance = strongResistances[0];

  // Bias: بالای PP = BUY, زیر PP = SELL
  const bias =
    pp !== null && current > pp
      ? "buy"
      : pp !== null && current < pp
        ? "sell"
        : "neutral";

  // ------- محاسبه‌ی پلن -------
  let entry = current;
  let stopLoss: number | null = null;
  let takeProfit: number | null = null;
  let riskReward: number | null = null;

  // ATR تقریبی از نوسان کندل‌ها
  const atr = current * 0.02;  // ~2% برای 1h

  if (bias === "buy") {
    entry = current;
    // SL: نزدیک‌ترین گزینه
    const supportSL = nearestSupport
      ? Number(nearestSupport.price) * 0.995
      : s1
        ? s1 * 0.995
        : null;
    const atrSL = current - 1.5 * atr;

    // هر کدوم نزدیک‌تر و منطقی‌تر باشه
    if (supportSL && Math.abs(current - supportSL) / current <= 0.04) {
      stopLoss = supportSL;
    } else {
      stopLoss = atrSL;
    }

    // TP: اولین مقاومت، یا R1، یا ATR-based
    if (nearestResistance) {
      takeProfit = Number(nearestResistance.price);
    } else if (r1 && r1 > current * 1.01) {
      takeProfit = r1;
    } else {
      takeProfit = current + 2.5 * atr;
    }
  } else if (bias === "sell") {
    entry = current;
    const resistanceSL = nearestResistance
      ? Number(nearestResistance.price) * 1.005
      : r1
        ? r1 * 1.005
        : null;
    const atrSL = current + 1.5 * atr;

    if (resistanceSL && Math.abs(resistanceSL - current) / current <= 0.04) {
      stopLoss = resistanceSL;
    } else {
      stopLoss = atrSL;
    }

    if (nearestSupport) {
      takeProfit = Number(nearestSupport.price);
    } else if (s1 && s1 < current * 0.99) {
      takeProfit = s1;
    } else {
      takeProfit = current - 2.5 * atr;
    }
  }

  if (stopLoss && takeProfit) {
    const risk = Math.abs(entry - stopLoss);
    const reward = Math.abs(takeProfit - entry);
    if (risk > 0) riskReward = reward / risk;
  }

  const biasConfig = {
    buy: {
      label: "تمایل به خرید 🟢",
      color: "text-emerald-400",
      bg: "border-emerald-500/30 bg-emerald-500/5",
      icon: TrendingUp,
    },
    sell: {
      label: "تمایل به فروش 🔴",
      color: "text-red-400",
      bg: "border-red-500/30 bg-red-500/5",
      icon: TrendingDown,
    },
    neutral: {
      label: "بی‌طرف ⚪",
      color: "text-zinc-400",
      bg: "border-white/10",
      icon: Crosshair,
    },
  }[bias];

  const BiasIcon = biasConfig.icon;

  // خطوط پلن
  const lines: PlanLine[] = [];
  if (nearestResistance) {
    lines.push({
      label: "نزدیک‌ترین مقاومت",
      price: nearestResistance.price,
      color: "text-red-400",
      icon: TrendingDown,
    });
  }
  if (pp) {
    lines.push({
      label: "Pivot Point (مرکز)",
      price: String(pp),
      color: "text-amber-400",
      icon: Target,
    });
  }
  if (nearestSupport) {
    lines.push({
      label: "نزدیک‌ترین حمایت",
      price: nearestSupport.price,
      color: "text-emerald-400",
      icon: TrendingUp,
    });
  }

  return (
    <Card className={cn("border-2", biasConfig.bg)}>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Crosshair className={cn("h-5 w-5", biasConfig.color)} />
            پلن معاملاتی
          </CardTitle>
          <Badge
            variant="outline"
            className={cn("border-2 text-sm", biasConfig.color, biasConfig.bg)}
          >
            <BiasIcon className="mr-1 h-3 w-3" />
            {biasConfig.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Map */}
        <div className="space-y-1.5">
          {lines.map((line, i) => {
            const Icon = line.icon;
            const price = Number(line.price);
            const diff = ((current - price) / current) * 100;
            return (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  {Icon && <Icon className={cn("h-4 w-4", line.color)} />}
                  <span className="text-sm">{line.label}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={cn("font-mono text-sm font-semibold", line.color)}>
                    {formatPrice(line.price)}
                  </span>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    ({diff >= 0 ? "+" : ""}
                    {diff.toFixed(2)}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Plan */}
        {(stopLoss || takeProfit) && (
          <div className="rounded-lg border border-white/10 bg-black/20 p-4">
            <p className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <ArrowRight className="h-4 w-4 text-emerald-400" />
              استراتژی پیشنهادی برای {bias === "buy" ? "خرید" : "فروش"}:
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <PlanBox
                label="ورود (Entry)"
                value={formatPrice(String(entry))}
                color="text-blue-400"
                icon={Target}
              />
              {stopLoss && (
                <PlanBox
                  label="حد ضرر (SL)"
                  value={formatPrice(String(stopLoss))}
                  color="text-red-400"
                  icon={Shield}
                  hint={`${(
                    (Math.abs(entry - stopLoss) / entry) *
                    100
                  ).toFixed(2)}% ریسک`}
                />
              )}
              {takeProfit && (
                <PlanBox
                  label="حد سود (TP)"
                  value={formatPrice(String(takeProfit))}
                  color="text-emerald-400"
                  icon={TrendingUp}
                  hint={`${(
                    (Math.abs(takeProfit - entry) / entry) *
                    100
                  ).toFixed(2)}% سود`}
                />
              )}
            </div>

            {riskReward && (
              <div className="mt-3 flex items-center justify-between rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2">
                <span className="text-xs text-muted-foreground">
                  نسبت ریسک به ریوارد
                </span>
                <span
                  className={cn(
                    "font-mono text-lg font-bold",
                    riskReward >= 2
                      ? "text-emerald-400"
                      : riskReward >= 1
                        ? "text-amber-400"
                        : "text-red-400",
                  )}
                >
                  1 : {riskReward.toFixed(2)}
                </span>
              </div>
            )}

            {riskReward && (
              <p className="mt-2 text-[10px] text-muted-foreground">
                {riskReward >= 2
                  ? "✅ نسبت عالی — ارزش ورود داره"
                  : riskReward >= 1
                    ? "⚠️ نسبت متوسط — با احتیاط"
                    : "❌ نسبت ضعیف — صبر کن"}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PlanBox({
  label,
  value,
  color,
  icon: Icon,
  hint,
}: {
  label: string;
  value: string;
  color: string;
  icon: React.ElementType;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-white/5 bg-card px-3 py-2.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-muted-foreground">{label}</span>
        <Icon className={cn("h-3.5 w-3.5", color)} />
      </div>
      <p className={cn("mt-1 font-mono text-sm font-bold", color)}>{value}</p>
      {hint && <p className="text-[10px] text-muted-foreground">{hint}</p>}
    </div>
  );
}
