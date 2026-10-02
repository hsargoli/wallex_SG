from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.api.v1.router import router as v1_router

app = FastAPI(title="ROSHD_SARV API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All v1 routes (markets, bots, profitability, simulation, ...)
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "Welcome to ROSHD_SARV Backend (DDD Architecture)"}
