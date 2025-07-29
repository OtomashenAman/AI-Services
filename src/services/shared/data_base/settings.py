# settings.py
from src.config.settings import settings


# load_dotenv() # Loads variables from a .env file

# --- Vector Database Settings for Qdrant (for Vectors) ---
QDRANT_URL = settings.qdrant_url
QDRANT_API_KEY = settings.qdrant_api_key
QDRANT_COLLECTION_NAME = "rag_vector_collection"
QDRANT_QCOLLECTION_NAME = "QuestionCollection"

# --- Metadata Database Settings for PostgreSQL (for Text and Metadata) ---
DB_USER = settings.db_user
DB_PASSWORD =settings.db_password
DB_HOST = settings.db_host
DB_PORT = settings.db_port
DB_NAME = settings.db_name

DB_URL  = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{ DB_PORT}/{ DB_NAME}"

# This will be the table where LlamaIndex stores the text and metadata of each node
DOCSTORE_TABLE_NAME = "rag_document_nodes"
