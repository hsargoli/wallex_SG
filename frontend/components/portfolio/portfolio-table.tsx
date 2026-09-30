"use client";

import { Lock } from "lucide-react";
import { type PortfolioItem } from "@/lib/api";
import { formatNumber, formatPrice } from "@/lib/format";
import { Badge } from "@/components/ui/badge";

type PriceSource = "bid" | "last";

function AssetIcon({ asset }: { asset: string }) {
  const isTmn = asset === "TMN" || asset === "IRT";
  return (
    <div
      className={`flex h-10 w-10 items-center justify-center rounded-lg font-mono text-[10px] font-bold ${
        isTmn
          ? "bg-gradient-to-br from-emerald-500/30 to-emerald-500/0 text-emerald-400"
          : "bg-gradient-to-br from-blue-500/20 to-blue-500/0 text-blue-400"
      }`}
    >
      {asset.slice(0, 3)}
    </div>
  );
}

export function PortfolioTable({
  items,
  priceSource,
}: {
  items: PortfolioItem[];
  priceSource: PriceSource;
}) {
  const isBid = priceSource === "bid";

  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      {/* Header */}
      <div className="hidden grid-cols-12 gap-4 border-b bg-muted/30 px-4 py-3 text-[11px] font-medium text-muted-foreground md:grid">
        <div className="col-span-3">دارایی</div>
        <div className="col-span-2 text-left">مقدار</div>
        <div className="col-span-2 text-left">
          قیمت واحد {isBid ? "(bid)" : "(last)"}
        </div>
        <div className="col-span-3 text-left">
          ارزش {isBid ? "برداشت" : "اسمی"}
        </div>
        <div className="col-span-2 text-left">سهم</div>
      </div>

      <div className="divide-y">
        {items.map((item) => {
          const locked = Number(item.locked) > 0;

          const priceUsdt = isBid ? item.price_usdt_bid : item.price_usdt_last;
          const priceTmn = isBid ? item.price_tmn_bid : item.price_tmn_last;
          const valueTmn = isBid ? item.value_tmn_bid : item.value_tmn_last;
          const valueUsdt = isBid ? item.value_usdt_bid : item.value_usdt_last;
          const sharePct = isBid ? item.share_pct_bid : item.share_pct_last;

          return (
            <div
              key={item.asset}
              className="grid grid-cols-1 gap-3 px-4 py-4 transition hover:bg-white/[0.02] md:grid-cols-12 md:gap-4 md:py-3"
            >
              {/* Asset */}
              <div className="col-span-3 flex items-center gap-3">
                <AssetIcon asset={item.asset} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-sm font-semibold">
                      {item.asset}
                    </p>
                    {locked && (
                      <Badge
                        variant="outline"
                        className="border-amber-500/30 text-[9px] text-amber-400"
                      >
                        <Lock className="mr-1 h-2 w-2" />
                        فریز
                      </Badge>
                    )}
                  </div>
                  <p className="truncate text-[11px] text-muted-foreground">
                    {item.fa_name ?? "—"}
                  </p>
                </div>
              </div>

              {/* Amount */}
              <div className="col-span-2 text-left">
                <p className="font-mono text-sm">
                  {formatNumber(item.available, {
                    maximumFractionDigits: 6,
                  })}
                </p>
                {locked && (
                  <p className="text-[10px] text-amber-400">
                    {formatNumber(item.locked, {
                      maximumFractionDigits: 4,
                    })}{" "}
                    قفل
                  </p>
                )}
              </div>

              {/* Unit price */}
              <div className="col-span-2 text-left">
                {priceUsdt && Number(priceUsdt) > 0 ? (
                  <>
                    <p className="font-mono text-xs text-foreground">
                      ${formatPrice(priceUsdt)}
                    </p>
                    <p className="font-mono text-[10px] text-muted-foreground">
                      {formatNumber(priceTmn ?? 0, {
                        maximumFractionDigits: 0,
                      })}{" "}
                      TMN
                    </p>
                  </>
                ) : (
                  <span className="text-[10px] text-muted-foreground/50">
                    بدون قیمت
                  </span>
                )}
              </div>

              {/* Total value */}
              <div className="col-span-3 text-left">
                {valueTmn ? (
                  <>
                    <p
                      className={`font-mono text-sm font-bold ${
                        isBid ? "text-emerald-400" : "text-blue-400"
                      }`}
                    >
                      {formatNumber(valueTmn, {
                        maximumFractionDigits: 0,
                      })}{" "}
                      TMN
                    </p>
                    {valueUsdt && (
                      <p className="font-mono text-[11px] text-muted-foreground">
                        ≈ $
                        {formatNumber(valueUsdt, {
                          maximumFractionDigits: 2,
                        })}
                      </p>
                    )}
                  </>
                ) : (
                  <span className="text-[10px] text-muted-foreground/50">
                    —
                  </span>
                )}
              </div>

              {/* Share */}
              <div className="col-span-2 text-left">
                <div className="flex items-center gap-2">
                  <div className="h-1.5 w-full max-w-[60px] overflow-hidden rounded-full bg-white/5">
                    <div
                      className={`h-full ${
                        isBid
                          ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
                          : "bg-gradient-to-r from-blue-500 to-blue-400"
                      }`}
                      style={{
                        width: `${Math.min(Number(sharePct), 100)}%`,
                      }}
                    />
                  </div>
                  <p className="font-mono text-xs text-muted-foreground">
                    {Number(sharePct).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
