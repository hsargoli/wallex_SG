from typing import List, Optional


class BaseStrategy:
    """اینترفیس پایه‌ی همه‌ی استراتژی‌ها"""

    def on_tick(self, price: float) -> str:
        """
        ورودی: قیمت لحظه‌ای
        خروجی: "BUY" | "SELL" | "HOLD"
        """
        raise NotImplementedError


class SimpleTrendStrategy(BaseStrategy):
    """
    استراتژی کراس EMA.

    - EMA سریع (پیش‌فرض ۵) بالای EMA کند (پیش‌فرض ۲۰) → BUY
    - EMA سریع زیر EMA کند → SELL
    - در غیر این صورت → HOLD

    چون از قیمت‌های قبلی برای محاسبه‌ی EMA استفاده می‌کنه،
    باید on_tick رو با قیمت‌های متوالی صدا زد.
    """

    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        if fast_period >= slow_period:
            raise ValueError("fast_period باید کمتر از slow_period باشه")

        self.fast_period = fast_period
        self.slow_period = slow_period

        self.prices: List[float] = []
        self.ema_fast: Optional[float] = None
        self.ema_slow: Optional[float] = None

        self.in_position = False

    # ------------------------------------------------------------
    # محاسبه EMA تدریجی
    # فرمول: EMA_new = price * k + EMA_prev * (1 - k)
    #         k = 2 / (period + 1)
    # ------------------------------------------------------------
    @staticmethod
    def _update_ema(prev_ema: Optional[float], price: float, period: int) -> float:
        k = 2.0 / (period + 1)
        if prev_ema is None:
            return price
        return price * k + prev_ema * (1 - k)

    def on_tick(self, price: float) -> str:
        self.prices.append(price)

        # آپدیت EMAها
        self.ema_fast = self._update_ema(self.ema_fast, price, self.fast_period)
        self.ema_slow = self._update_ema(self.ema_slow, price, self.slow_period)

        # تا وقتی EMA کند شکل نگرفته (چند کندل اول)، کاری نکن
        if len(self.prices) < self.slow_period:
            return "HOLD"

        # کراس صعودی: fast بالای slow → بخر
        if self.ema_fast > self.ema_slow and not self.in_position:
            self.in_position = True
            return "BUY"

        # کراس نزولی: fast زیر slow → بفروش
        if self.ema_fast < self.ema_slow and self.in_position:
            self.in_position = False
            return "SELL"

        return "HOLD"
