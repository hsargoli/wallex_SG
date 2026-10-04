"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback } from "react";

const VALID_TF = ["15m", "1h", "4h", "1D"] as const;
export type ScanTf = (typeof VALID_TF)[number];

export interface ScannerUrlState {
  tf: ScanTf;
  page: number;
  signal: string;      // "all" | "buy" | "sell" | "hold"
  strength: string;    // "all" | "weak" | "medium" | "strong"
  quote: "all" | "TMN" | "USDT";
  rsiMin: number | null;
  rsiMax: number | null;
  rrMin: number | null;
  search: string;
}

const DEFAULTS: ScannerUrlState = {
  tf: "1h",
  page: 1,
  signal: "all",
  strength: "all",
  quote: "all",
  rsiMin: null,
  rsiMax: null,
  rrMin: null,
  search: "",
};

function parseNum(v: string | null): number | null {
  if (v === null || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function useScannerUrlState() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const tfParam = params.get("tf");
  const tf: ScanTf = (VALID_TF as readonly string[]).includes(tfParam ?? "")
    ? (tfParam as ScanTf)
    : DEFAULTS.tf;

  const state: ScannerUrlState = {
    tf,
    page: Math.max(1, Number(params.get("page")) || 1),
    signal: params.get("signal") || DEFAULTS.signal,
    strength: params.get("strength") || DEFAULTS.strength,
    quote: (params.get("quote") as "TMN" | "USDT" | null) || DEFAULTS.quote,
    rsiMin: parseNum(params.get("rsiMin")),
    rsiMax: parseNum(params.get("rsiMax")),
    rrMin: parseNum(params.get("rrMin")),
    search: params.get("search") || DEFAULTS.search,
  };

  const update = useCallback(
    (patch: Partial<ScannerUrlState>) => {
      const next = { ...state, ...patch };
      const sp = new URLSearchParams();

      if (next.tf !== DEFAULTS.tf) sp.set("tf", next.tf);
      if (next.page > 1) sp.set("page", String(next.page));
      if (next.signal !== DEFAULTS.signal) sp.set("signal", next.signal);
      if (next.strength !== DEFAULTS.strength) sp.set("strength", next.strength);
      if (next.quote !== DEFAULTS.quote) sp.set("quote", next.quote);
      if (next.rsiMin !== null) sp.set("rsiMin", String(next.rsiMin));
      if (next.rsiMax !== null) sp.set("rsiMax", String(next.rsiMax));
      if (next.rrMin !== null) sp.set("rrMin", String(next.rrMin));
      if (next.search.trim()) sp.set("search", next.search.trim());

      const qs = sp.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [state, pathname, router],
  );

  const reset = useCallback(() => {
    router.replace(pathname, { scroll: false });
  }, [pathname, router]);

  return { state, update, reset };
}
