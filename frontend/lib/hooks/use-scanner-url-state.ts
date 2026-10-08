"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback } from "react";

const VALID_TF = ["15m", "1h", "4h", "1D"] as const;
export type ScanTf = (typeof VALID_TF)[number];

export type EmaCross = "all" | "bullish" | "bearish";
export type MacdSide = "all" | "positive" | "negative";
export type BbZone = "all" | "low" | "mid" | "high";

export interface ScannerUrlState {
  tf: ScanTf;
  page: number;
  quote: "all" | "TMN" | "USDT";
  emaCross: EmaCross;
  macdSide: MacdSide;
  bbZone: BbZone;
  rsiMin: number | null;
  rsiMax: number | null;
  atrMin: number | null;
  search: string;
}

const DEFAULTS: ScannerUrlState = {
  tf: "1h",
  page: 1,
  quote: "all",
  emaCross: "all",
  macdSide: "all",
  bbZone: "all",
  rsiMin: null,
  rsiMax: null,
  atrMin: null,
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
    quote: (params.get("quote") as "TMN" | "USDT" | null) || DEFAULTS.quote,
    emaCross: (params.get("emaCross") as EmaCross | null) || DEFAULTS.emaCross,
    macdSide: (params.get("macdSide") as MacdSide | null) || DEFAULTS.macdSide,
    bbZone: (params.get("bbZone") as BbZone | null) || DEFAULTS.bbZone,
    rsiMin: parseNum(params.get("rsiMin")),
    rsiMax: parseNum(params.get("rsiMax")),
    atrMin: parseNum(params.get("atrMin")),
    search: params.get("search") || DEFAULTS.search,
  };

  const update = useCallback(
    (patch: Partial<ScannerUrlState>) => {
      const next = { ...state, ...patch };
      const sp = new URLSearchParams();
      if (next.tf !== DEFAULTS.tf) sp.set("tf", next.tf);
      if (next.page > 1) sp.set("page", String(next.page));
      if (next.quote !== DEFAULTS.quote) sp.set("quote", next.quote);
      if (next.emaCross !== DEFAULTS.emaCross) sp.set("emaCross", next.emaCross);
      if (next.macdSide !== DEFAULTS.macdSide) sp.set("macdSide", next.macdSide);
      if (next.bbZone !== DEFAULTS.bbZone) sp.set("bbZone", next.bbZone);
      if (next.rsiMin !== null) sp.set("rsiMin", String(next.rsiMin));
      if (next.rsiMax !== null) sp.set("rsiMax", String(next.rsiMax));
      if (next.atrMin !== null) sp.set("atrMin", String(next.atrMin));
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
