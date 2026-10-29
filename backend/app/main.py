import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import Request
from app.services.auth import AuthError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.infrastructure.exchange.wallex.ticker_ws import WallexTickerClient
from app.services.bots.nooaah.scheduler import (
    NooaahScheduler,
    set_scheduler,
)
from app.services.bots.sarv_router.scheduler import SarvRouterScheduler
from app.presentation.api.v1.realtime import TickerFanout, router as realtime_router
from app.presentation.api.v1.router import router as v1_router
from app.services.guest import GuestScheduler
from app.services.prefetch import CandlePrefetcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: setup/teardown."""
    # --- Startup ---
    configure_logging()
    settings = get_settings()
    exchange = WallexExchange.create(settings)
    app.state.exchange = exchange
    app.state.settings = settings

    # Real-time ticker (Wallex Socket.IO)
    loop = asyncio.get_running_loop()
    fanout = TickerFanout(loop)
    ticker_client = WallexTickerClient(on_tick=fanout.on_tick)
    app.state.ticker_fanout = fanout
    app.state.ticker_client = ticker_client
    ticker_client.start()

    # Nooaah scheduler (hourly paper cycle)
    nooaah_sched = NooaahScheduler(exchange=exchange, interval_minutes=30)
    nooaah_sched.start()
    app.state.nooaah_scheduler = nooaah_sched
    set_scheduler(nooaah_sched)

    # SarvRouter scheduler (Phase 2A: ticks every 30min)
    sarv_sched = SarvRouterScheduler(interval_minutes=30)
    sarv_sched.start()
    app.state.sarv_scheduler = sarv_sched

    # Guest Mode — paper engines + shared scheduler
    app.state.guest_engines = {}
    guest_sched = GuestScheduler(interval_sec=180)
    guest_sched.set_engines_provider(lambda: app.state.guest_engines)
    # User Mode — paper engines برای کاربران لاگین‌شده (فاز ۱۷.۷.۲)
    app.state.user_engines = {}
    guest_sched.set_user_engines_provider(lambda: app.state.user_engines)
    guest_sched.start()
    app.state.guest_scheduler = guest_sched

    # Candle prefetcher: warms top-N symbol candle cache every 5 min
    # (top_n=10, ~11% wallex duty cycle — CTO 2026-10-24).
    prefetcher = CandlePrefetcher(
        exchange=exchange,
        top_n=settings.PREFETCH_TOP_N,
        interval_sec=settings.PREFETCH_INTERVAL_SEC,
    )
    prefetch_task = asyncio.create_task(prefetcher.run())
    app.state.prefetcher = prefetcher
    app.state.prefetch_task = prefetch_task

    try:
        yield
    finally:
        # --- Shutdown ---
        from app.services.order_chase.worker import manager as chase_manager

        await chase_manager.stop_all()
        ticker_client.stop()
        nooaah_sched.stop()
        app.state.sarv_scheduler.stop()
        await guest_sched.stop()
        # Stop prefetcher before closing the exchange
        prefetcher = getattr(app.state, "prefetcher", None)
        prefetch_task = getattr(app.state, "prefetch_task", None)
        if prefetcher is not None:
            prefetcher.stop()
        if prefetch_task is not None:
            prefetch_task.cancel()
            try:
                await prefetch_task
            except asyncio.CancelledError:
                pass
        await exchange.aclose()


app = FastAPI(title="ROSHD_SARV API", lifespan=lifespan)
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


# ---------- Rate Limiting ----------
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """پاسخ 429 با پیام فارسی."""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"محدودیت نرخ درخواست. "
                f"لطفاً کمی صبر کن و دوباره تلاش کن. "
                f"(limit: {exc.detail})"
            ),
        },
    )


# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sarvbots.ir",
        "https://www.sarvbots.ir",
        # local dev
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3020",
        "http://127.0.0.1:3020",
    ],
    allow_credentials=False,   # ما cookie نداریم، فقط header
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Guest-Token", "Authorization"],
    max_age=3600,
)

# ---------- Routes ----------
app.include_router(v1_router)
app.include_router(realtime_router)  # /ws/ticker/{symbol}


@app.get("/")
async def root():
    return {"message": "Welcome to ROSHD_SARV Backend (DDD Architecture)"}


@app.get("/health")
async def health():
    """Health check برای monitoring و frontend."""
    return {"status": "ok", "service": "wallex-backend"}
