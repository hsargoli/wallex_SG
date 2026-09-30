"""Balance — موجودی یک دارایی در کیف پول کاربر."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Balance:
    asset: str
    available: Decimal
    locked: Decimal
    total: Decimal
    fa_name: str | None = None
    en_name: str | None = None
