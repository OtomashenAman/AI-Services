from enum import Enum, auto
from pydantic import BaseModel,field_validator
from typing import Dict


from . import settings
from .retrievers import VectorDBRetriever
from .generators import (
    QuestionAnswerGenerator,
    InformationCollectorGenerator,
    StructuredOutputGenerator,
)

class RAGType(Enum):
    """Defines the types of RAG pipeline configurations available."""
    QUESTION_ANSWER = "QUESTION_ANSWER"
    INFORMATION_COLLECTOR = "INFORMATION_COLLECTOR"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"


# --- Mapping from RAGType to Components ---
# This allows for easy extension with new retrievers or generators
retriever_map = {
    RAGType.QUESTION_ANSWER: VectorDBRetriever,
    RAGType.INFORMATION_COLLECTOR: VectorDBRetriever,
    RAGType.STRUCTURED_OUTPUT: VectorDBRetriever,
}

generator_map = {
    RAGType.QUESTION_ANSWER: (QuestionAnswerGenerator, {"llm": settings.Settings.llm}),
    RAGType.INFORMATION_COLLECTOR: (InformationCollectorGenerator, {"llm": settings.Settings.llm}),
    RAGType.STRUCTURED_OUTPUT: (StructuredOutputGenerator, {"llm": settings.STRUCTURED_OUTPUT_LLM}),
}




class RAGRequestModel(BaseModel):
    queries : dict[str,str]
    user_type : str
    rag_type : RAGType

    @field_validator("queries")
    @classmethod
    def validate_queries(cls, queries: Dict[str, str]) -> Dict[str, str]:
        if not queries:
            raise ValueError("queries must not be empty")

        for key, question in queries.items():
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"Query for ID '{key}' must be a non-empty string")
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Query ID '{key}' must be a non-empty string")
        return queries