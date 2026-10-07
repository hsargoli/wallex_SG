from decimal import Decimal as D

from app.services.order_chase.logic import Action, decide

T = D("0.01")


def L(*pairs):
    return [(D(str(p)), D(str(q))) for p, q in pairs]


def buy(bids, asks, own=None, qty="0", **kw):
    return decide("BUY", L(*bids), L(*asks), D("0.70"), D("0.80"), T,
                  own_price=None if own is None else D(str(own)), own_qty=D(qty), **kw)


def test_buy_places_one_tick_above_top_capped():
    d = buy([(0.79, 10), (0.75, 5)], [(0.82, 3)])
    assert (d.action, d.price) == (Action.PLACE, D("0.80"))


def test_buy_waits_when_price_above_range():
    assert buy([(0.90, 10)], [(0.92, 3)]).action == Action.WAIT


def test_buy_never_exceeds_cap():
    d = buy([(0.80, 10)], [(0.85, 3)])
    assert d.price == D("0.80")


def test_buy_one_tick_spread_joins_top():
    d = buy([(0.79, 10)], [(0.80, 3)])
    assert (d.action, d.price) == (Action.PLACE, D("0.79"))


def test_buy_lowers_when_book_moves_down_excluding_own_order():
    d = buy([(0.80, 10), (0.75, 5)], [(0.82, 3)], own=0.80, qty="10")
    assert (d.action, d.price) == (Action.MOVE, D("0.76"))


def test_buy_raises_when_outbid_but_not_above_cap():
    d = buy([(0.79, 4), (0.78, 10)], [(0.82, 3)], own=0.78, qty="10")
    assert (d.action, d.price) == (Action.MOVE, D("0.80"))


def test_buy_keeps_when_already_best_and_alone():
    d = buy([(0.80, 10)], [(0.82, 3)], own=0.80, qty="10")
    assert d.action == Action.KEEP


def test_buy_hysteresis():
    d = buy([(0.79, 4), (0.78, 10)], [(0.82, 3)], own=0.79, qty="1", min_move_ticks=2)
    assert d.action == Action.KEEP


def test_buy_floor_enforced():
    d = buy([(0.60, 5)], [(0.65, 3)], enforce_bound=True)
    assert d.action == Action.WAIT
    d = buy([(0.60, 5), (0.69, 2)], [(0.65, 3)], own=0.69, qty="2", enforce_bound=True)
    assert d.action in (Action.CANCEL, Action.KEEP)


def test_sell_mirror():
    d = decide("SELL", L((1.15, 3)), L((1.21, 5), (1.25, 2)), D("1.20"), D("1.30"), T)
    assert (d.action, d.price) == (Action.PLACE, D("1.20"))


def test_sell_never_below_floor_and_waits_below_range():
    d = decide("SELL", L((1.05, 3)), L((1.10, 5)), D("1.20"), D("1.30"), T)
    assert d.action == Action.WAIT


def test_sell_raises_when_book_moves_up_excluding_own():
    d = decide("SELL", L((1.15, 3)), L((1.21, 10), (1.28, 5)), D("1.20"), D("1.30"), T,
               own_price=D("1.21"), own_qty=D("10"))
    assert (d.action, d.price) == (Action.MOVE, D("1.27"))
