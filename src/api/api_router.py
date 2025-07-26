from fastapi import APIRouter
from src.services.RAG.routes import rag_router

api_router = APIRouter()

@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

api_router.include_router(rag_router, prefix="/RAG", tags=["RAG"])