from fastapi import APIRouter,Depends

from src.services.ingestion.routes import ingest_router
from src.services.rag.routes import rag_router
from src.core.auth import get_auth_user,get_cached_auth_user

api_router = APIRouter()

@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

api_router.include_router(ingest_router, prefix="/ingest", tags=["ingest"],dependencies=[Depends(get_auth_user)])
api_router.include_router(rag_router,prefix="/rag",tags=['rag'],dependencies=[Depends(get_cached_auth_user)])