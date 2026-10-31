/**
 * Paper Trading — shared SYMBOLS array (DRY ManualOrderForm).
 * Extracted from /guest and /paper-trading/manual pages.
 *
 * Structure matches the original: { key, fa } as const.
 */

export const SYMBOLS = [
  { key: "BTCTMN",  fa: "بیت‌کوین" },
  { key: "ETHTMN",  fa: "اتریوم" },
  { key: "USDTTMN", fa: "تتر" },
  { key: "SOLTMN",  fa: "سولانا" },
  { key: "XRPTMN",  fa: "ریپل" },
] as const;

export type SymbolEntry = (typeof SYMBOLS)[number];
