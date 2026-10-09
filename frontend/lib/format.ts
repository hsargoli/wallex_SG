export function formatNumber(
  value: string | number,
  options?: Intl.NumberFormatOptions,
): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    ...options,
  }).format(num);
}

export function formatPrice(value: string | number): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 8,
  }).format(num);
}

export function formatPct(value: string | number): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return "—";
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}

export function formatTime(ts: number, withYear = false): string {
  if (!ts || ts <= 0) return "—";
  try {
    return new Date(ts * 1000).toLocaleString("en-GB", {
      ...(withYear ? { year: "numeric" as const } : {}),
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

export function formatClock(ts: number | null | undefined): string {
  if (!ts || ts <= 0) return "—";
  return new Date(ts * 1000).toLocaleTimeString("en-GB", { hour12: false });
}

export function formatDay(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString("en-GB", { month: "short", day: "numeric" });
}


/**
 * قیمت را هوشمند فرمت می‌کند — بر اساس بزرگی عدد:
 *   >= 1000    →  1,469         (بدون اعشار)
 *   >= 1       →  1.0058        (تا ۴ رقم)
 *   >= 0.01    →  0.0500        (تا ۶ رقم)
 *   < 0.01     →  0.000123      (تا ۸ رقم)
 */
export function formatPriceSmart(value: string | number): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return "—";
  const abs = Math.abs(num);

  let maxDigits: number;
  if (abs >= 1000) maxDigits = 0;
  else if (abs >= 1) maxDigits = 4;
  else if (abs >= 0.01) maxDigits = 6;
  else maxDigits = 8;

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: maxDigits,
    minimumFractionDigits: 0,
  }).format(num);
}
