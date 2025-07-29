# rag/generators.py
import logging
from typing import List, Any
from abc import ABC, abstractmethod

from llama_index.core import get_response_synthesizer
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.prompts import PromptTemplate
from llama_index.core.schema import NodeWithScore
from llama_index.core.llms import LLM
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr

logger = logging.getLogger(__name__)


class BaseGenerator(BaseModel, ABC):
    """
    Abstract base class for all response generators.

    Defines the common interface for generating a response based on a query
    and a set of retrieved document nodes. The generator is responsible for
    synthesizing the final output.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())

    llm: LLM

    @abstractmethod
    def custom_query(self, query_str: str, nodes: List[NodeWithScore]) -> Any:
        """
        The method that subclasses must implement to generate a response.

        Args:
            query_str (str): The original user query.
            nodes (List[NodeWithScore]): The list of retrieved nodes from the retriever.

        Returns:
            Any: The generated response, which can be a string, a Pydantic model, etc.
        """
        pass

# --- Pydantic Model for Structured Output ---
class AnswerWithSources(BaseModel):
    """A Pydantic model for a structured answer with source citations."""
    answer: str = Field(
        description="A comprehensive and detailed answer to the user's question."
    )
    sources: List[str] = Field(
        description="A list of source document names used to formulate the answer."
    )


class QuestionAnswerGenerator(BaseGenerator):
    """
    A generator that synthesizes a direct, natural language answer to a question.
    """
    _response_synthesizer: Any = PrivateAttr()

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # Uses the default 'compact' response mode
        self._response_synthesizer = get_response_synthesizer(llm=self.llm)
        logger.info("Initialized QuestionAnswerGenerator.")

    def custom_query(self, query_str: str, nodes: List[NodeWithScore]) -> str:
        """
        Synthesizes a direct answer from the given nodes.
        """
        logger.info("Synthesizing a direct answer for query: '%s'", query_str)
        response = self._response_synthesizer.synthesize(query_str, nodes)
        logger.debug("Generated response: %s", str(response))
        return str(response)


class InformationCollectorGenerator(BaseGenerator):
    """
    A generator that collects and returns all information from retrieved nodes.
    """
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        logger.info("Initialized InformationCollectorGenerator.")

    def custom_query(self, query_str: str, nodes: List[NodeWithScore]) -> str:
        """
        Concatenates the text content of the provided nodes.
        """
        logger.info(
            "Collecting information for query: '%s' from %d nodes",
            query_str, len(nodes)
        )
        if not nodes:
            return "No relevant information found."

        full_text = "\n\n---\n\n".join(
            [f"Source: {node.metadata.get('file_name', 'N/A')}\n\n{node.get_content()}" for node in nodes]
        )
        logger.debug("Collected text length: %d chars", len(full_text))
        return full_text


class StructuredOutputGenerator(BaseGenerator):
    """
    A generator that produces a response in a predefined Pydantic structure.
    """
    _output_parser: PydanticOutputParser = PrivateAttr()
    _qa_template: PromptTemplate = PrivateAttr()
    _response_synthesizer: Any = PrivateAttr()

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._output_parser = PydanticOutputParser(output_cls=AnswerWithSources)
        self._qa_template = PromptTemplate(
            "Some information is provided below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given this information, please answer the query.\n"
            "Query: {query_str}\n\n"
            "Format your response as a JSON object with the following keys: \n"
            "{format_instructions}\n"
        )
        self._response_synthesizer = get_response_synthesizer(
            llm=self.llm,
            response_mode="refine",
            output_parser=self._output_parser,
            text_qa_template=self._qa_template,
        )
        logger.info("Initialized StructuredOutputGenerator.")

    def custom_query(self, query_str: str, nodes: List[NodeWithScore]) -> AnswerWithSources:
        """
        Generates a response conforming to the Pydantic model from the given nodes.
        """
        logger.info("Generating structured output for query: '%s'", query_str)
        response = self._response_synthesizer.synthesize(
            query=query_str,
            nodes=nodes,
            format_instructions=self._output_parser.get_format_instructions(),
        )
        logger.debug("Generated structured response: %s", response.dict())
        return response
