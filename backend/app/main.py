from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.presentation.api.v1 import markets, paper_v2, simulation

app = FastAPI(title="ROSHD_SARV Trading Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(markets.router, prefix="/v1/markets", tags=["Markets"])
app.include_router(paper_v2.router, prefix="/v1/paper-v2", tags=["Paper Trading V2"])
app.include_router(simulation.router, prefix="/v1/simulation", tags=["Simulation Engine"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ROSHD_SARV"}
