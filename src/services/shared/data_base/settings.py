# settings.py
from src.config.settings import settings


# load_dotenv() # Loads variables from a .env file

# --- Vector Database Settings for Qdrant (for Vectors) ---
QDRANT_URL = settings.qdrant_url
QDRANT_API_KEY = settings.qdrant_api_key
QDRANT_COLLECTION_NAME = "rag_vector_collection"
QDRANT_QCOLLECTION_NAME = "QuestionCollection"



DB_URL  = settings.DATABASE_URL

# This will be the table where LlamaIndex stores the text and metadata of each node
DOCSTORE_TABLE_NAME = "rag_document_nodes"
