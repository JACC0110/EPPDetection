from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.video_routes import router

app = FastAPI()

# Allow the web UI and other origins to call this API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)
