from fastapi import APIRouter

rag_router = APIRouter()

@rag_router.get("/ping")
async def ping():
    return {"message": "RAG service is running"}

