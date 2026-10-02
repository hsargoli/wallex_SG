from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.presentation.api.v1.markets import router as markets_router
from app.presentation.api.v1.paper_v2 import router as paper_router
from app.presentation.api.v1.simulation import router as sim_router

app = FastAPI(title="ROSHD_SARV API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(markets_router, prefix="/v1/markets", tags=["Markets"])
app.include_router(paper_router, prefix="/v1/paper-trading", tags=["Paper Trading V2"])
app.include_router(sim_router, prefix="/v1/simulation", tags=["Simulation"])

@app.get("/")
async def root():
    return {"message": "Welcome to ROSHD_SARV Backend (DDD Architecture)"}
