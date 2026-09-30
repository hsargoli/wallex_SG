"""Profitability checker service.

Given an order book snapshot (best_bid, best_ask) and a fee model, evaluates
whether a round-trip trade (buy → sell) is profitable.
"""

from decimal import Decimal

from app.domain.models.profitability import (
    FeeConfig,
    ProfitabilityRequest,
    ProfitabilityResponse,
)

# Use a large precision context for financial math
HUNDRED = Decimal("100")


def _round_money(value: Decimal) -> Decimal:
    """Quantize a monetary value to a reasonable precision (8 decimals)."""
    return value.quantize(Decimal("0.00000001"))


def _round_pct(value: Decimal) -> Decimal:
    """Quantize a percentage value to 8 decimals."""
    return value.quantize(Decimal("0.00000001"))


class ProfitabilityService:
    """Evaluates whether a trade is profitable after fees and slippage."""

    def __init__(self, fee_config: FeeConfig | None = None) -> None:
        self.fee_config = fee_config or FeeConfig()

    def evaluate(
        self,
        *,
        request: ProfitabilityRequest,
        best_bid: Decimal,
        best_ask: Decimal,
    ) -> ProfitabilityResponse:
        """
        Evaluate profitability of a round-trip trade.

        The idea:
          - Buy the asset (at ask for taker, at bid for maker)
          - Sell the asset (at bid for taker, at ask for maker)
          - Subtract fees and slippage
          - If net_profit > 0, the trade is profitable.
        """
        if best_bid <= 0 or best_ask <= 0:
            raise ValueError("best_bid and best_ask must be positive")
        if best_ask < best_bid:
            raise ValueError("best_ask must be greater than or equal to best_bid")

        capital = request.capital
        notes: list[str] = []

        # Determine fee rate for this request
        if request.maker_fee_rate is not None:
            applied_fee_rate = request.maker_fee_rate
        elif request.taker_fee_rate is not None:
            applied_fee_rate = request.taker_fee_rate
        elif request.order_type == "maker":
            applied_fee_rate = self.fee_config.maker_fee_rate
        else:
            applied_fee_rate = self.fee_config.taker_fee_rate

        spread = best_ask - best_bid
        mid = (best_ask + best_bid) / Decimal("2")
        spread_pct = (spread / mid) * HUNDRED if mid > 0 else Decimal("0")

        slippage_pct = request.slippage_pct if request.order_type == "taker" else Decimal("0")
        slippage_factor = slippage_pct / HUNDRED

        # Effective prices
        if request.order_type == "maker":
            # Assume we can buy at bid and sell at ask (ideal limit fills)
            effective_buy_price = best_bid
            effective_sell_price = best_ask
            if slippage_pct > 0:
                notes.append("Slippage ignored for maker orders.")
        else:
            # Taker buys at ask, sells at bid, both worsened by slippage
            effective_buy_price = best_ask * (Decimal("1") + slippage_factor)
            effective_sell_price = best_bid * (Decimal("1") - slippage_factor)

        # Quantity bought with capital at effective buy price
        quantity = capital / effective_buy_price if effective_buy_price > 0 else Decimal("0")

        # Gross profit from price movement
        gross_profit = (effective_sell_price - effective_buy_price) * quantity

        # Fees (charged on notional)
        buy_notional = effective_buy_price * quantity
        sell_notional = effective_sell_price * quantity
        buy_fee = buy_notional * applied_fee_rate
        sell_fee = sell_notional * applied_fee_rate

        # Slippage cost (only meaningful for taker)
        if request.order_type == "taker" and slippage_pct > 0:
            slippage_cost = (
                best_ask - effective_buy_price + effective_sell_price - best_bid
            ) * quantity
            # Note: gross_profit already accounts for slippage, so we only report
            # the extra cost for transparency.
        else:
            slippage_cost = Decimal("0")

        total_cost = buy_fee + sell_fee
        net_profit = gross_profit - total_cost

        net_profit_pct = (net_profit / capital) * HUNDRED if capital > 0 else Decimal("0")

        # Minimum spread needed to break even, in absolute price units.
        # Derivation: gross = (ask - bid) * qty; fees ≈ (ask + bid) * qty * fee_rate
        # Setting net = 0: (ask - bid) = (ask + bid) * fee_rate
        # For small fees: min_spread ≈ 2 * mid * fee_rate
        min_profitable_spread = (best_ask + best_bid) * applied_fee_rate

        if not net_profit > 0:
            notes.append("Spread does not cover fees; trade is not profitable at current fee rate.")

        return ProfitabilityResponse(
            symbol=request.symbol,
            order_type=request.order_type,
            best_bid=_round_money(best_bid),
            best_ask=_round_money(best_ask),
            spread=_round_money(spread),
            spread_pct=_round_pct(spread_pct),
            capital=_round_money(capital),
            applied_fee_rate=applied_fee_rate,
            slippage_pct=slippage_pct,
            effective_buy_price=_round_money(effective_buy_price),
            effective_sell_price=_round_money(effective_sell_price),
            gross_profit=_round_money(gross_profit),
            buy_fee=_round_money(buy_fee),
            sell_fee=_round_money(sell_fee),
            slippage_cost=_round_money(slippage_cost),
            total_cost=_round_money(total_cost),
            net_profit=_round_money(net_profit),
            net_profit_pct=_round_pct(net_profit_pct),
            min_profitable_spread=_round_money(min_profitable_spread),
            is_profitable=net_profit > 0,
            notes=notes,
        )


# Global singleton
profitability_service = ProfitabilityService()
