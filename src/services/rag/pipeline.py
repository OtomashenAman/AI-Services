# rag/pipeline.py
import logging
from abc import ABC, abstractmethod
from .generators import BaseGenerator
from .retrievers import BaseRetriever
from llama_index.core.postprocessor.types import BaseNodePostprocessor

logger = logging.getLogger(__name__)


class BasePipeline(ABC):
    """
    Abstract base class for all RAG pipelines.

    Defines the common interface for executing a query.
    """
    @abstractmethod
    def query(self, query_str: str):
        """
        Runs the query through the pipeline.
        """
        pass


class RAGPipeline(BasePipeline):
    """
    Orchestrates the RAG process by combining a retriever and a generator.
    """

    def __init__(self, retriever: BaseRetriever, node_postprocessors: list[BaseNodePostprocessor], generator: BaseGenerator):
        """
        Initializes the RAG pipeline.

        Args:
            retriever (BaseRetriever): The retriever instance to fetch nodes.
            generator (BaseGenerator): The generator instance to produce the final response.
        """
        self.retriever = retriever
        self.node_postprocessors = node_postprocessors
        self.generator = generator
        logger.info(
            "RAGPipeline initialized with retriever '%s' and generator '%s'",
            retriever.__class__.__name__,
            generator.__class__.__name__
        )

    def query(self, query_str: str):
        """
        Executes a query through the RAG pipeline.

        It first uses the retriever to fetch relevant context, then passes
        that context to the generator to synthesize a final answer.

        Args:
            query_str (str): The user's input query.

        Returns:
            The response from the generator.
        """
        logger.info("--- New Query Pipeline Start ---")
        logger.info("Executing query: '%s'", query_str)

        logger.info("Step 1: Retrieving nodes from %s...", self.retriever.__class__.__name__)
        nodes = self.retriever.retrieve(query_str)
        logger.info("Step 1: Retrieved %d nodes.", len(nodes))

        logger.info("Step 2: Post-processing nodes...")
        for postprocessor in self.node_postprocessors:
            nodes = postprocessor.postprocess_nodes(nodes)
        logger.info("Step 2: Post-processed to %d nodes.", len(nodes))

        logger.info("Step 3: Generating response with %s...", self.generator.__class__.__name__)
        response = self.generator.custom_query(query_str, nodes)

        logger.info("--- Query Pipeline End ---")
        return response
