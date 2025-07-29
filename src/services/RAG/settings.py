from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import openai


from src.config.settings import settings



openai.api_key  = settings.OPENAI_API_KEY
# --- LLM and Embedding Model Configuration ---
# Using the Settings singleton for global configuration
Settings.llm = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# --- Retriever Configuration ---
SIMILARITY_TOP_K = 5  # Number of top similar nodes to retrieve

# --- Generator Configuration ---
# You can define model-specific settings for generators if needed
# For example, a different model for structured data extraction
STRUCTURED_OUTPUT_LLM = OpenAI(model="gpt-4o-mini")

MAIN_JSON_REQUIRED_FIELDS = {"queries", "tenant_id", "rag_type"}

