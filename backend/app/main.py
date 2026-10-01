from fastapi import FastAPI
from app.api.endpoints.simulation import router as simulation_router

app = FastAPI(title="Wallex Platform")

# رجیستر کردن روت جدید
app.include_router(simulation_router, prefix="/v1/simulation", tags=["Simulation"])

@app.get("/")
def read_root():
    return {"status": "online"}
