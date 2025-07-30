# rag/rag_service.py
import logging
import sys



from src.services.shared.data_base.storage_context import get_qa_vector_storage_context
from src.services.rag.post_processors import TenantFilterPostprocessor, QA_dataadditionPostprocessor
from src.services.rag.models import RAGType, retriever_map, generator_map
from src.services.rag.retrievers import BaseRetriever
from src.services.rag.generators import BaseGenerator
from src.services.rag.pipeline import RAGPipeline


logger = logging.getLogger(__name__)


class QA_RAGService():
    """
    Service for Question Answering using RAG (Retrieval-Augmented Generation).
    This service initializes the retriever and generator based on the specified
    RAG type and provides a method to get responses from the configured pipeline.
    This is specific to the QA use case, where the retriever fetches relevant Question-Answer pairs
    from a vector database, and the generator synthesizes a response based on those pairs.
    """
    def __init__(self, rag_type: RAGType,request):
        """
        Initializes the QA_RAGService with the specified RAG type.
        """
        logger.info("Initializing QA_RAGService for type: %s", rag_type.name)
        self.rag_type = rag_type
        self.request = request
        
        try:
            self.storage_context = get_qa_vector_storage_context()
        except Exception as e:
            logger.error("Failed to get storage context: %s", e)
            logger.error("Please ensure your database is running and accessible.")
            sys.exit(1)

        # --- Component Initialization from Maps ---
        retriever_class = retriever_map.get(rag_type)
        generator_info = generator_map.get(rag_type)

        if not retriever_class or not generator_info:
            raise ValueError(f"Unknown RAGType provided: {rag_type}")

        generator_class, generator_kwargs = generator_info

        # Initialize the components once
        self.retriever: BaseRetriever = retriever_class(storage_context=self.storage_context,
                                                        request=request)
        self.node_postprocessors = [
            TenantFilterPostprocessor(request=self.request),
            QA_dataadditionPostprocessor()
        ]

        self.generator: BaseGenerator = generator_class(retriever=self.retriever, **generator_kwargs)
        
        # Initialize the pipeline once
        self.pipeline = RAGPipeline(retriever=self.retriever, node_postprocessors=self.node_postprocessors, generator=self.generator)
        logger.info("QA_RAGService for %s initialized successfully.", self.rag_type.name)

    def get_response(self, query: str):
        """
        Generic API endpoint to get a response from the configured RAG pipeline.

        Args:
            query (str): The user's input query.

        Returns:
            The response from the executed pipeline.
        """
        logger.info("Executing 'get_response' for service type: %s", self.rag_type.name)
        return self.pipeline.query(query)
