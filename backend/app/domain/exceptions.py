"""ارورهای دامنه — مستقل از هر فریمورک و کتابخانه خارجی."""


class DomainError(Exception):
    """کلاس پایه همه ارورهای دامنه."""

    def __init__(self, message: str, *, code: str = "domain_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ExchangeError(DomainError):
    """خطای مربوط به صرافی (شبکه، احراز هویت، پاسخ نامعتبر)."""


class ExchangeAuthError(ExchangeError):
    """کلید API نامعتبر یا رد شده."""


class ExchangeRateLimitError(ExchangeError):
    """Rate Limit صرافی."""


class ExchangeUnavailableError(ExchangeError):
    """صرافی در دسترس نیست (5xx، تایم‌اوت، شبکه)."""


class InvalidSymbolError(DomainError):
    """نماد معاملاتی نامعتبر یا ناشناخته."""
