from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.api_router import api_router
from src.config.settings import settings
from src.core.logging_config import setup_logging

# calling the logging setup function to configure logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME,debug= settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)