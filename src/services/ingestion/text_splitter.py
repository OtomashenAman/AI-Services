# text_splitter.py
import logging
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser import NodeParser
from fastapi.requests import Request

logger = logging.getLogger(__name__)

def get_node_parser(request:Request) -> NodeParser:
    """
    Initializes and returns a LlamaIndex `NodeParser` using a `SentenceSplitter`.

    This parser splits input text into smaller chunks based on sentence boundaries,
    using the configured `chunk_size` and `chunk_overlap` settings. The resulting nodes
    are suitable for indexing, embedding, and retrieval tasks in vector-based pipelines.

    Returns:
        NodeParser: A `SentenceSplitter` instance configured with custom chunking behavior.
    """
    logger.info(
        "Initializing SentenceSplitter with chunk_size=%d and overlap=%d",
        request.state.CHUNK_SIZE,
        request.state.CHUNK_OVERLAP
    )

    return SentenceSplitter(
        chunk_size= request.state.CHUNK_SIZE,
        chunk_overlap=request.state.CHUNK_OVERLAP
    )