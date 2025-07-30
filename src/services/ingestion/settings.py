# settings.py
from src.config.settings import settings

# --- LlamaIndex Project/Observability Settings ---
PROJECT_NAME =  "rag-ingestion-pipeline"

# --- LLM Model Settings ---
LLM_MODEL_NAME = "gpt-4o-mini"

# --- Embedding Model Settings (for LlamaIndex) ---
OPENAI_API_KEY = settings.OPENAI_API_KEY
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536 # 'text-embedding-3-small' produces 1536-dimensional vectors

# --- Node Parser (Text Splitter) Settings ---
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

REQUIRED_FIELDS = {"question", "answer"}
