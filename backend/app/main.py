from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.presentation.api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: setup/teardown."""
    # --- Startup ---
    configure_logging()
    settings = get_settings()
    exchange = WallexExchange.create(settings)
    app.state.exchange = exchange
    app.state.settings = settings

    try:
        yield
    finally:
        # --- Shutdown ---
        await exchange.aclose()


app = FastAPI(title="ROSHD_SARV API", lifespan=lifespan)

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
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routes ----------
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "Welcome to ROSHD_SARV Backend (DDD Architecture)"}


@app.get("/health")
async def health():
    """Health check برای monitoring و frontend."""
    return {"status": "ok", "service": "wallex-backend"}
