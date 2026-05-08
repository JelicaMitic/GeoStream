from fastapi import FastAPI
from app.routers import drivers, rides
from app.database import engine
from app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GeoStream API")

app.include_router(drivers.router)
app.include_router(rides.router)

@app.get("/")
def root():
    return {"message": "GeoStream API radi!"}