import logging
from typing import List
from abc import ABC, abstractmethod
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever as LlamaBaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from fastapi.requests import Request

from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from  .settings import SIMILARITY_TOP_K


logger = logging.getLogger(__name__)


class BaseRetriever(LlamaBaseRetriever, ABC):
    """
    Abstract base class for all custom retrievers in this RAG project.

    This class defines the essential interface that any retriever must implement.
    It inherits from LlamaIndex's BaseRetriever to ensure compatibility with
    the rest of the framework (like generators and pipelines).

    To create a new custom retriever, you should inherit from this class and
    implement the `_retrieve` method.
    """

    @abstractmethod
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        The core retrieval logic that subclasses must implement.

        This method takes a query and should return a list of relevant nodes,
        each with a similarity score.

        Args:
            query_bundle (QueryBundle): An object containing the query string
                and other metadata.

        Returns:
            List[NodeWithScore]: A list of document nodes with their scores.
        """
        pass


class VectorDBRetriever(BaseRetriever):
    """
    A concrete retriever that fetches nodes from a VectorStoreIndex.

    This retriever is responsible for querying the vector database to find the
    most relevant document chunks (nodes) based on a user's query. It returns
    these nodes along with their similarity scores.
    """

    def __init__(self, storage_context: StorageContext,request:Request):
        """
        Initializes the retriever.

        Args:
            storage_context (StorageContext): The storage context containing
                the vector store, document store, and index store.
        """
        logger.info("Initializing VectorDBRetriever...")
        self._index = VectorStoreIndex.from_documents(
            [], storage_context=storage_context
        )

        Metadata_filters = MetadataFilters(
                    filters=[
                        ExactMatchFilter(key="user_type", value=request.state.user_type)
                    ]
                )


        # This internal retriever from the index will do the heavy lifting
        self._retriever = self._index.as_retriever(
            similarity_top_k=SIMILARITY_TOP_K,
            filters=Metadata_filters
            
        )
        super().__init__()
        logger.info(
            "VectorDBRetriever initialized with similarity_top_k=%d",
            SIMILARITY_TOP_K,
        )

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Implementation of the retrieval logic for the vector database.

        This method delegates the query to the underlying LlamaIndex retriever
        configured with the specified top-k similarity.

        Args:
            query_bundle (QueryBundle): The query bundle containing the query string.

        Returns:
            List[NodeWithScore]: A list of nodes with their corresponding similarity scores.
        """
        query_str = query_bundle.query_str
        logger.info("Retrieving nodes for query: '%s'", query_str)

        retrieved_nodes = self._retriever.retrieve(query_str)

        logger.info(
            "Retrieved %d nodes.", len(retrieved_nodes)
        )
        if retrieved_nodes:
            logger.debug(
                "Top retrieved node score: %.4f", retrieved_nodes[0].get_score()
            )
        return retrieved_nodes
