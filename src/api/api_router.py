from fastapi import APIRouter,Depends

from src.services.ingestion.routes import ingest_router
from src.services.rag.routes import rag_router

api_router = APIRouter()

@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

api_router.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
api_router.include_router(rag_router,prefix="/rag",tags=['rag'])