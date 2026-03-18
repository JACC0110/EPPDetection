from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.detection_routes import router
from app.database.db import Base, engine, ensure_schema

Base.metadata.create_all(bind=engine)
ensure_schema()

app = FastAPI(
    title="PPE Detection Service"
)

# Expose saved violation images to clients (e.g., web UI)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.include_router(router)