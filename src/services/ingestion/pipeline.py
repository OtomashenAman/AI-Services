# data_ingestion_service.py
import logging
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.schema import TransformComponent
from typing import List
from fastapi import Request

# Import the factory functions from our submodules
from src.services.ingestion.doc_loader import get_document_reader,get_qa_document_reader,get_qa_input_reader
from src.services.ingestion.text_splitter import get_node_parser
from src.services.ingestion.embedding_provider import get_embedding_model
from src.services.shared.data_base.storage_context import get_storage_context,get_qa_vector_storage_context
from .settings import LLM_MODEL_NAME



logger = logging.getLogger(__name__)

def run_pipeline(
    document_reader_fn,
    storage_context_fn,
    document_loader:bool = False,
    input_data: list[dict] = None,
    request:Request =None,
) -> dict:
    """
    Runs a generic ingestion pipeline that processes documents (from file or memory),
    generates embeddings, and stores the results using LlamaIndex components.

    This function supports both file-based and in-memory ingestion modes depending on
    the `document_loader` flag. It uses a configurable reader, parser, embedding model,
    and storage context.

    Args:
        document_reader_fn (Callable): 
            A function that either returns:
            - A reader object with a `.load_data()` method (for file ingestion), or
            - A direct processor that accepts `input_data` (for in-memory ingestion).
        storage_context_fn (Callable): A function that returns a `StorageContext` instance.
        document_loader (bool, optional): 
            If True, calls `.load_data()` on the output of `document_reader_fn()`.
            If False, passes `input_data` directly into the reader function.
        input_data (list[dict], optional): 
            A list of structured documents (typically Q&A format) to be ingested when using in-memory mode.

    Returns:
        dict: {
            "processed": List of document IDs that were successfully processed and embedded.
            "unprocessed": List of document IDs (from `input_data`) that were skipped or failed.
        }

    """
    logger.info("--- Pipeline Service Started ---")
    
    # --- 1. Initialize Components ---
    logger.info("Initializing components from submodules...")
    node_parser = get_node_parser(request)
    embed_model = get_embedding_model()

    # --- 2. Configure Global Settings ---
    logger.info("Configuring global LlamaIndex settings...")
    Settings.llm = OpenAI(model=LLM_MODEL_NAME)
    Settings.node_parser = node_parser
    Settings.embed_model = embed_model
    Settings.num_workers = 4

    # --- 3. Load Documents ---
    documents = None
 
    if document_loader:
        reader = document_reader_fn(request)
        documents = reader.load_data()
    else:
        documents = document_reader_fn(input_data,request)
    
    if not documents:
        logger.warning("No documents found in the source directory.")
        return {"processed": [], "unprocessed": input_data or []}

    # --- 4. Setup Storage and Pipeline ---
    storage_context = storage_context_fn()
    pipeline = create_ingestion_pipeline(
        storage_context=storage_context,
        transformations=[node_parser, embed_model]
    )

     # --- 5. Run Pipeline ---
    nodes = pipeline.run(documents=documents)
    logger.info("Ingestion complete.")
    
    processed_ids = set()
    for node in nodes:
        metadata = node.metadata or {}
        # Prefer 'doc_id', fallback to 'id' or node_id
        doc_id = metadata.get('doc_id') or metadata.get('id') or node.node_id
        processed_ids.add(str(doc_id))

    
    # --- 6. Identify Unprocessed Items ---
    unprocessed = []
    if input_data:
        for item in input_data:
            item_id = str(item.get('doc_id') or item.get('id'))
            if item_id not in processed_ids:
                unprocessed.append(item_id)

    return {
        "processed": list(processed_ids),
        "unprocessed": unprocessed
    }

# ----------------- Pipeline Entry Points -----------------

def run_ingestion_pipeline(request:Request) -> list[dict]:
    """
    Executes the end-to-end ingestion pipeline for file-based document ingestion.

    This function:
    - Initializes a document reader to load files from the source directory
    - Uses the default storage context
    - Parses and embeds the documents
    - Stores the processed nodes in the configured vector store

    It is designed for batch ingestion of documents from disk using `SimpleDirectoryReader`.

    Returns:
        list[dict]: A dictionary with two keys:
            - "processed": List of document IDs that were successfully ingested
            - "unprocessed": List of document IDs that were skipped or failed
    """
    return run_pipeline(
        document_reader_fn=get_document_reader,
        storage_context_fn=get_storage_context,
        document_loader=True
    )

def run_question_pipeline(request:Request) -> list[dict]:
    """
    Runs the ingestion pipeline specifically for Q&A documents from the file system.

    This function:
    - Uses `CustomQADirectoryReader` to load `.json` and `.csv` Q&A files from the source directory
    - Stores the embedded results using the Q&A-specific vector storage context
    - Processes and indexes the documents using LlamaIndex components

    Returns:
        list[dict]: A dictionary with:
            - "processed": List of successfully ingested Q&A document IDs
            - "unprocessed": List of document IDs that were skipped or failed during processing
    """
    return run_pipeline(
        document_reader_fn=get_qa_document_reader,
        storage_context_fn=get_qa_vector_storage_context,
        document_loader=True,
        request=request
    )

def run_input_json_pipeline(qa_list: list[dict],request:Request) -> list[dict]:
    """
    Runs the ingestion pipeline for in-memory Q&A data (e.g., from an API request).

    This function:
    - Accepts a list of Q&A dictionaries (each with fields like 'id' and 'question')
    - Converts them into `TextNode` objects using `get_qa_input_reader`
    - Processes, embeds, and stores them using the Q&A-specific storage context

    Args:
        qa_list (list[dict]): List of structured Q&A entries to be ingested.

    Returns:
        list[dict]: A dictionary with:
            - "processed": List of successfully ingested Q&A document IDs
            - "unprocessed": List of input entries that were skipped or failed
    """
    return run_pipeline(
        document_reader_fn=get_qa_input_reader,
        storage_context_fn=get_qa_vector_storage_context,
        document_loader=False,
        input_data=qa_list,
        request=request,
        
    )


def create_ingestion_pipeline(storage_context: StorageContext, transformations: List[TransformComponent]) -> IngestionPipeline:
    """
    Creates and returns a configured LlamaIndex `IngestionPipeline` instance.

    This pipeline is responsible for:
    - Applying a series of transformation components (e.g., node parser, embedding model)
    - Storing processed nodes in the provided hybrid storage context
      (which includes a vector store and a document store)

    Args:
        storage_context (StorageContext): The storage backend for the pipeline,
            containing both a vector store and a document store.
        transformations (List[TransformComponent]): A list of transformation components
            to apply during ingestion, such as parsing and embedding.

    Returns:
        IngestionPipeline: A ready-to-run ingestion pipeline that applies transformations
        and persists data to the configured storage layers.

    """
    logger.info("Creating LlamaIndex IngestionPipeline for hybrid storage...")

    # The pipeline will use the components from the transformations
    # (like the node_parser and embed_model) and the storage_context.
    pipeline = IngestionPipeline(
        transformations=transformations,
        vector_store=storage_context.vector_store,
        docstore=storage_context.docstore
    )
    
    logger.info("IngestionPipeline created successfully.")
    return pipeline