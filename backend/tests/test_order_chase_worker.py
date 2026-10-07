import asyncio
from decimal import Decimal as D
from types import SimpleNamespace as NS

from app.services.order_chase.worker import ChaseConfig, ChaseWorker, validate_market


class FakeEx:
    def __init__(self):
        self.placed, self.canceled, self.orders = [], [], {}
        self.cancel_exec, self.fail_cancel = D(0), False

    async def get_market(self, s):
        return NS(tick_size=D("0.01"), step_size=D("0.1"), min_notional=D("1"),
                  min_quantity=D("0.1"), quote_precision=2)

    async def place_order(self, req):
        self.placed.append(req)
        return req

    async def cancel_order(self, cid, sym):
        if self.fail_cancel:
            raise RuntimeError("boom")
        self.canceled.append(cid)
        return NS(client_id=cid, executed_qty=self.cancel_exec)

    async def get_orders(self, symbol=None, status=None):
        return list(self.orders.values())


def L(pairs):
    return [(D(str(p)), D(str(q))) for p, q in pairs]


def mk(ex, dry=True, can=True, side="BUY", qty="10"):
    cfg = ChaseConfig("XTMN", side, D("0.70"), D("0.80"), D(qty), dry_run=dry, max_notional=D("100"))
    return ChaseWorker(cfg, ex, lambda: can)


def book(w, bids, asks):
    async def f():
        return L(bids), L(asks)
    w._book = f


def run(c):
    return asyncio.run(c)


def test_dry_run_never_calls_exchange_orders():
    ex = FakeEx(); w = mk(ex); book(w, [(0.75, 5)], [(0.82, 3)])
    run(w.step())
    assert ex.placed == [] and w.own.price == D("0.76") and w.last_action == "PLACE"


def test_live_blocked_when_trading_disabled():
    ex = FakeEx(); w = mk(ex, dry=False, can=False); book(w, [(0.75, 5)], [(0.82, 3)])
    run(w.step())
    assert ex.placed == [] and w.status == "error"


def test_live_places_limit_with_chase_prefix():
    ex = FakeEx(); w = mk(ex, dry=False); book(w, [(0.75, 5)], [(0.82, 3)])
    run(w.step())
    r = ex.placed[0]
    assert r.price == D("0.76") and r.quantity == D("10") and r.client_id.startswith("chase-")
    assert r.type.value == "LIMIT" and r.side.value == "BUY"


def _placed(ex, w):
    cid = ex.placed[0].client_id
    ex.orders[cid] = NS(client_id=cid, executed_qty=D(0), is_open=True)
    return cid


def test_move_cancels_then_places_only_remaining():
    ex = FakeEx(); w = mk(ex, dry=False); book(w, [(0.75, 5)], [(0.82, 3)])
    run(w.step()); cid = _placed(ex, w)
    book(w, [(0.76, 10), (0.70, 5)], [(0.82, 3)])
    ex.cancel_exec = D("3")
    run(w.step())
    assert ex.canceled == [cid] and len(ex.placed) == 2
    assert ex.placed[1].price == D("0.71") and ex.placed[1].quantity == D("7")
    assert w.filled == D("3") and w.moves == 1


def test_cancel_failure_does_not_place_again():
    ex = FakeEx(); w = mk(ex, dry=False); book(w, [(0.75, 5)], [(0.82, 3)])
    run(w.step()); _placed(ex, w)
    book(w, [(0.76, 10), (0.70, 5)], [(0.82, 3)])
    ex.fail_cancel = True
    try:
        run(w.step()); raised = False
    except RuntimeError:
        raised = True
    assert raised and len(ex.placed) == 1


def test_filled_order_finishes():
    ex = FakeEx(); w = mk(ex, dry=False); book(w, [(0.75, 5)], [(0.82, 3)])
    run(w.step()); cid = ex.placed[0].client_id
    ex.orders[cid] = NS(client_id=cid, executed_qty=D("10"), is_open=False)
    run(w.step())
    assert w.status == "done" and len(ex.placed) == 1


def test_max_notional_blocks_oversized_order():
    ex = FakeEx(); w = mk(ex, dry=False, qty="200"); book(w, [(0.75, 5)], [(0.82, 3)])
    try:
        run(w.step()); raised = False
    except ValueError:
        raised = True
    assert raised and ex.placed == []


def test_validate_market():
    m = NS(step_size=D("0.1"), min_quantity=D("0.1"), min_notional=D("1"))
    ok = ChaseConfig("X", "BUY", D("0.7"), D("0.8"), D("10"))
    small = ChaseConfig("X", "BUY", D("0.7"), D("0.8"), D("0.5"))
    assert validate_market(ok, m) is None and validate_market(small, m) is not None


def test_stop_cancels_open_live_order():
    ex = FakeEx(); w = mk(ex, dry=False); book(w, [(0.75, 5)], [(0.82, 3)])

    async def go():
        w.start()
        await asyncio.sleep(0.1)
        await w.stop()

    run(go())
    assert w.status == "stopped" and ex.canceled == [ex.placed[0].client_id]
