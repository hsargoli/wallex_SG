/**
 * Paper Trading — shared formatting helpers (DRY ManualOrderForm).
 * Extracted from /guest and /paper-trading/manual pages.
 * Matches original behavior exactly.
 */

/** "21686999673" → "21,686,999,673" (English comma — input only accepts digits+comma) */
export function formatNum(s: string): string {
  const digits = s.replace(/[^0-9]/g, "");
  if (!digits) return "";
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/** "21,686,999,673" → "21686999673" (only digits) */
export function parseNum(s: string): string {
  return s.replace(/[^0-9]/g, "");
}

/**
 * 1234.56 → "۱٬۲۳۵" (Persian locale, rounded to integer).
 * Note: this is for Toman/integer display. For decimals, use chart-legend's fmt.
 */
export const fmt = (n: number | undefined | null): string =>
  n == null ? "—" : Math.round(n).toLocaleString("fa-IR");

/**
 * 1234.5678 → "۱٬۲۳۴٫۵۷" (Persian locale, N digits after decimal).
 * Use for percentages and PnL with decimal precision.
 */
export const fmtNum = (n: number | undefined | null, digits: number = 2): string =>
  n == null ? "—" : n.toLocaleString("fa-IR", { maximumFractionDigits: digits });
