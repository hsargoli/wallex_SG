"""Symbol — نماد معاملاتی مثل BTCUSDT یا XLMTMN."""

from dataclasses import dataclass

from app.domain.exceptions import InvalidSymbolError


@dataclass(frozen=True, slots=True)
class Symbol:
    """نماد معاملاتی — immutable و قابل استفاده در dict/set."""

    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().upper()
        if not v or len(v) < 4 or not v.isalnum():
            raise InvalidSymbolError(f"نماد نامعتبر: {self.value!r}")
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
