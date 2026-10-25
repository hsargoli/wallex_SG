"use client";

import { useMemo } from "react";
import { useMarkets, useAllSignals } from "@/lib/queries";
import { CosmosCanvas } from "@/components/cosmos/cosmos-canvas";

/**
 * Market Cosmos (ADR 0031) — isolated MVP.
 * Fetches top-50 TMN markets by volume, generates signals (from cache),
 * passes to Canvas for progressive reveal. Zero backend changes.
 */
export default function CosmosPage() {
  const markets = useMarkets();

  const top50 = useMemo(() => {
    if (!markets.data?.items) return [];
    return [...markets.data.items]
      .filter((m) => String(m.symbol).toUpperCase().endsWith("TMN"))
      .sort(
        (a, b) =>
          Number(b.daily_quote_volume || 0) -
          Number(a.daily_quote_volume || 0),
      )
      .slice(0, 50)
      .map((m) => m.symbol);
  }, [markets.data]);

  const signals = useAllSignals(top50, "1h");
  const isLoading = markets.isLoading || signals.isLoading;

  return (
    <div className="h-[calc(100vh-3rem)] w-full overflow-hidden rounded-xl border border-white/10">
      <CosmosCanvas
        signals={signals.data?.signals ?? []}
        isLoading={isLoading}
      />
    </div>
  );
}
