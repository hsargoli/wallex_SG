// Helper functions مشترک بین signals و markets detail pages

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function signalConfig(signal?: string) {
  const map = {
    buy: {
      label: "خرید",
      color: "text-emerald-400",
      icon: TrendingUp,
    },
    sell: {
      label: "فروش",
      color: "text-red-400",
      icon: TrendingDown,
    },
    hold: {
      label: "بی‌طرف",
      color: "text-zinc-400",
      icon: Minus,
    },
  } as const;
  return map[(signal as keyof typeof map) || "hold"] || map.hold;
}

export function strengthLabel(s: string): string {
  return (
    {
      weak: "ضعیف",
      medium: "متوسط",
      strong: "قوی",
    }[s] || s
  );
}
