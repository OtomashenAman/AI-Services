# embedding_provider.py
import logging
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.embeddings import BaseEmbedding
from src.services.ingestion.settings import OPENAI_API_KEY,EMBEDDING_MODEL_NAME


logger = logging.getLogger(__name__)

def get_embedding_model() -> BaseEmbedding:
    """
    Initializes and returns an OpenAI embedding model instance for use in vector-based operations.

    This function uses configuration from the `settings` module to instantiate the `OpenAIEmbedding` model
    with the specified model name and API key. It is typically used to generate embeddings for documents,
    queries, or nodes when building vector indexes.

    Returns:
        BaseEmbedding: An instance of `OpenAIEmbedding` configured with the model name and API key.

    Raises:
        ValueError: If the OpenAI API key is missing in the environment variables.

    """
    logger.info("Initializing OpenAIEmbedding model: '%s'",  EMBEDDING_MODEL_NAME)
    
    if not  OPENAI_API_KEY:
        msg = "OPENAI_API_KEY not found in environment variables."
        logger.error(msg)
        raise ValueError(msg)

    return OpenAIEmbedding(
        model= EMBEDDING_MODEL_NAME,
        api_key= OPENAI_API_KEY
    )
