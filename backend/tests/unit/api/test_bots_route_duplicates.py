"""Guard: no duplicate routes in bots.py (TDD RED first)."""
from app.presentation.api.v1.bots import router


def test_no_duplicate_routes():
    """Each (method, path) pair must appear exactly once."""
    seen = {}
    for route in router.routes:
        if not hasattr(route, "methods") or not hasattr(route, "path"):
            continue
        for m in route.methods:
            key = (m, route.path)
            seen.setdefault(key, []).append(getattr(route, "name", "?"))
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    assert not dup, f"duplicate routes: {dup}"


def test_symbols_route_single():
    # Router may have a prefix (/bots), so use endswith.
    matches = [
        r for r in router.routes
        if hasattr(r, "path") and r.path.endswith("/{slug}/symbols")
        and hasattr(r, "methods") and "POST" in r.methods
    ]
    assert len(matches) == 1, (
        f"expected 1 POST .../{{slug}}/symbols, got {len(matches)}: "
        f"{[r.path for r in matches]}"
    )
