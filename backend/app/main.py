from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All v1 routes (markets, bots, profitability, simulation, orders, ...)
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "Welcome to ROSHD_SARV Backend (DDD Architecture)"}
