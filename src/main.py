from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.api_router import api_router
from src.config.settings import settings

app = FastAPI(title=settings.PROJECT_NAME,debug= settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)