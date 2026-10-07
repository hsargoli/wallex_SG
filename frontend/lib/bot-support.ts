// منبع واحد قابلیت‌های «تأییدشده»ی ربات‌ها. فقط چیزی را true کن که واقعاً کار می‌کند.
// توجه: تست زنده فعلاً با Paper v3 اجرا می‌شود که مخصوص scalp_master است.
export const SUPPORT: Record<string, { backtest: boolean; paper: boolean }> = {
  scalp_master: { backtest: true, paper: true },
  trend_follow: { backtest: true, paper: false },
  mean_revert: { backtest: true, paper: false },
  volatility_hunter: { backtest: true, paper: false },
  volatility_hunter_v2: { backtest: true, paper: false },
};

// ابزارهای غیرمعامله‌گر
export const NON_TRADING = new Set(["market_scanner"]);

export const botScore = (slug: string) =>
  (SUPPORT[slug]?.paper ? 2 : 0) + (SUPPORT[slug]?.backtest ? 1 : 0);
