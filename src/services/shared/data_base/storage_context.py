# vector_database.py
import logging
import qdrant_client
import sqlalchemy

from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.storage.index_store.postgres import PostgresIndexStore
from llama_index.storage.docstore.postgres import PostgresDocumentStore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Use an explicit relative import to find the settings module in the same package
from . import settings 

from llama_index.core.storage import StorageContext  

logger = logging.getLogger(__name__)


def connect_qdrantDB():
    qdrant_client_instance = qdrant_client.QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=120.0
        )
    
    return qdrant_client_instance 

def connect_postgres():
    return PostgresDocumentStore.from_params(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    table_name=settings.DOCSTORE_TABLE_NAME,  
    schema_name="public",   # default schema
)

def connect_postgres_index():
    return PostgresIndexStore.from_params(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD, 
    schema_name="public"
)

def create_postgres_session():
    """
    Creates a new SQLAlchemy session for PostgreSQL.
    Returns:
        Session: A new SQLAlchemy session object.
    """
    engine = create_engine(
        settings.DB_URL
    )
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def get_storage_context() -> StorageContext:
    """
    Creates and returns a LlamaIndex StorageContext with a QdrantVectorStore
    for embeddings, and a persistent PostgresDocumentStore and PostgresIndexStore for metadata.
    """
    logger.info("Setting up 3-component hybrid storage: Qdrant for vectors, PostgreSQL for docs and index.")

    try:
        # --- 1. Set up Qdrant for Vector Storage ---
        logger.info("Connecting to Qdrant at URL: %s", settings.QDRANT_URL)
        qdrant_client_instance = connect_qdrantDB()

        vector_store = QdrantVectorStore(
        client=qdrant_client_instance,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        batch_size=settings.Batch_size
            )
        logger.info("QdrantVectorStore initialized for collection: '%s'", settings.QDRANT_COLLECTION_NAME)

        # --- 2. Set up PostgreSQL for Document and Index Storage ---
        logger.info("Connecting to PostgreSQL at %s:%s for Docstore and IndexStore", settings.DB_HOST, settings.DB_PORT)
        pg_connection_string = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        
        engine = sqlalchemy.create_engine(pg_connection_string)
        with engine.connect() as connection:
            logger.debug("Successfully connected to PostgreSQL via SQLAlchemy.")
            
        # The Docstore will store the text content and metadata of each Node
        # Using the corrected class name
        docstore = PostgresDocumentStore.from_uri(
            uri = pg_connection_string,
            table_name= str(settings.DOCSTORE_TABLE_NAME),
            schema_name = 'public',

        )

        logger.info("PostgresDocumentStore initialized for table/namespace: '%s'", settings.DOCSTORE_TABLE_NAME)

        # The IndexStore will store the index's structural metadata
        # Using the corrected class name
        index_store = PostgresIndexStore.from_uri(
            uri=pg_connection_string,
        )
        logger.info("PostgresIndexStore initialized.")

        # --- 3. Create and return the combined StorageContext ---
        # All three components are now persistent.
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            # docstore=docstore,
            # index_store=index_store
        )
        logger.info("3-component hybrid StorageContext created successfully.")
        return storage_context

    except Exception as e:
        logger.error("Failed to set up hybrid storage context.", exc_info=True)
        raise


def get_qa_vector_storage_context() -> StorageContext:
    try:
        logger.info("Connecting to Qdrant at URL: %s", settings.QDRANT_URL)

        qdrant_client_instance = connect_qdrantDB()

        vector_store = QdrantVectorStore(
        client=qdrant_client_instance,
        collection_name=settings.QDRANT_QCOLLECTION_NAME,
    )
        

        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        logger.info("StorageContext created successfully.")
        return storage_context

    except Exception as e:
        logger.exception("Failed to set up vector storage context: %s", str(e))
        raise


