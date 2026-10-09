from fastapi import FastAPI
from app.routes.files import router as files_router
from app.database import engine, Base
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aereo Geospatial Measurement API",
    version="1.0.0"
)

app.include_router(files_router)


@app.get("/")
def root():
    return {"message": "API is running"}