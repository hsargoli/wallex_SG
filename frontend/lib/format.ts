export function formatNumber(
  value: string | number,
  options?: Intl.NumberFormatOptions,
): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return "—";
  return new Intl.NumberFormat("fa-IR", {
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
  return `${sign}${num.toFixed(4)}%`;
}

export function formatTime(ts: number, withYear = false): string {
  if (!ts || ts <= 0) return "—";
  try {
    return new Date(ts * 1000).toLocaleString("fa-IR", {
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
