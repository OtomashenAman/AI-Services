import logging
import json
import csv
from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import TextNode
from typing import List, Union, Iterable, Dict
from .settings import  REQUIRED_FIELDS
import os
from fastapi.requests import Request
from src.services.shared.data_base.qa_sql_writer import insert_qa_to_postgres,delete_qa_pairs_by_ids
from src.utils.sequence_reset import reset_qa_pairs_sequence
from src.services.shared.data_base.storage_context import create_postgres_session
from llama_index.core.schema import TextNode
logger = logging.getLogger(__name__)

# --------------------------------------------------------
#                   Utility Functions
# --------------------------------------------------------

def format_qa_documents(
    request: Request,
    data: Iterable[Dict],
    filename: str = None,
) -> List[TextNode]:

    nodes = []
    inserted_ids = []
    session = create_postgres_session()

    logger.info(f"User type for this request: {request.state.user_type}")

    for i, entry in enumerate(data):
        try:
            #  Validate required fields
            if not all(field in entry for field in REQUIRED_FIELDS):
                logger.warning(f"Skipping malformed entry in {filename}: {entry}")
                continue

            question = str(entry.get("question", "")).strip()
            if not question:
                logger.warning(f"Skipping entry with empty question in {filename}: {entry}")
                continue

            #   Attempt to insert into PostgreSQL
            try:
                doc_id = insert_qa_to_postgres(
                    question=question,
                    answer=entry.get("answer", ""),
                    user_type=request.state.user_type,
                    client_id=request.state.client_id,
                    EOR_id=request.state.EOR_id,
                    contrator_id=request.state.contrator_id,
                    session=session
                )
                inserted_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Failed to insert QAPair at index {i}. Rolling back this entry. Error: {e}")
                session.rollback()

                #  Fix sequence after failed insert
                try:
                    reset_qa_pairs_sequence(session)
                except Exception as seq_e:
                    logger.warning(f"Failed to reset sequence after rollback: {seq_e}")
                continue

            #   Add to vector store
            node = TextNode(
                text=f"Question: {question}",
                id_=str(doc_id),
                metadata={
                    "doc_id": str(doc_id),
                    "user_type": request.state.user_type,
                    "EOR_id": request.state.EOR_id,
                    "client_id": request.state.client_id,
                    "contrator_id": request.state.contrator_id
                }
            )
            nodes.append(node)
            logger.debug(f"Created TextNode with node_id: {node.node_id}")

        except Exception as e:
            logger.error(f"Unexpected error at index {i} in {filename}: {entry} | Error: {e}")
            continue  # Skip unexpected errors

    try:
        session.commit()
        logger.info(f"Committed {len(nodes)} successful inserts from {filename}")
    except Exception as e:
        logger.exception("Final commit failed. Rolling back entire session.")
        session.rollback()

        #  Delete manually inserted records (mimic rollback)
        try:
            if inserted_ids:
                delete_qa_pairs_by_ids(inserted_ids, session)
                session.commit()
                logger.warning(f"Cleaned up {len(inserted_ids)} partially inserted QAs")
        except Exception as delete_e:
            logger.error(f"Failed to delete inserted QAs after commit failure: {delete_e}")

        try:
            reset_qa_pairs_sequence(session)
        except Exception as seq_e:
            logger.warning(f"Failed to reset sequence after final rollback: {seq_e}")

        raise ValueError("Failed to commit data to PostgreSQL")

    finally:
        session.close()

    return nodes


# --------------------------------------------------------
#                   Document Readers
# --------------------------------------------------------

def get_document_reader(request:Request) -> SimpleDirectoryReader:
    """
    Initializes and returns a SimpleDirectoryReader instance from LlamaIndex,
    configured to read files from a predefined source directory.

    Each file ingested will be enriched with metadata, including:
    - 'filename': The name of the file being read.
    - 'user_type': The User identifier, used for filtering in multi-tenant environments.
    - 'doc_id'   : A unique identifier for the document, useful for tracking and updates.

    This reader is typically used to ingest documents (e.g., text, PDFs, JSON files) from a local
    directory and enrich them with metadata for downstream processing, indexing, or retrieval tasks.

    Returns:
        SimpleDirectoryReader: An instance configured to read and tag documents from the source directory.
    """
    source_dir = request.state.source_directory

    def metadata_fn(file_path:str)->Dict:
        return {
            "filename":os.path.basename(file_path),
            "user_type":request.state.user_type,
            "doc_id":request.state.doc_id
        }
    logger.info("Initializing SimpleDirectoryReader for path: '%s'",source_dir)
    return SimpleDirectoryReader(input_dir=source_dir,file_metadata=metadata_fn)


class CustomQADirectoryReader:
    """
    Custom directory reader for ingesting Q&A-style documents from a local directory.

    This class reads `.json` and `.csv` files containing structured Q&A entries,
    parses them, and returns a list of `TextNode` objects with custom `node_id`s
    and metadata for indexing in LlamaIndex.

    Each Q&A entry must include the required fields specified in `REQUIRED_FIELDS` (e.g., 'id', 'question').

    Attributes:
        input_dir (Union[str, Path]): Path to the directory containing input files.
    """

    def __init__(self, input_dir: Union[str, Path],request:Request):
        self.input_dir = Path(input_dir)
        self.request = request

    def load_data(self) -> List[TextNode]:
        """
        Loads and processes all `.json` and `.csv` files in the input directory.

        Returns:
            List[TextNode]: A combined list of parsed `TextNode` objects from all valid files.
                            Each node includes:
                            - Formatted text (e.g., "Question: ...")
                            - Custom node ID based on the Q&A entry's ID
                            - Metadata including 'doc_id' and 'user_type'

        Returns empty list if directory is invalid or contains no valid files.
        """
        all_nodes = []

        if not self.input_dir.exists() or not self.input_dir.is_dir():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return []

        for file in self.input_dir.glob("*"):
            suffix = file.suffix.lower()
            if suffix == ".json":
                logger.info(f"Processing JSON file: {file}")
                all_nodes.extend(self._load_json(file))
            elif suffix == ".csv":
                logger.info(f"Processing CSV file: {file}")
                all_nodes.extend(self._load_csv(file))
            else:
                logger.warning(f"Unsupported file type: {file}")

        return all_nodes

    def _load_json(self, file_path: Path) -> List[TextNode]:
        """
            Reads and parses a JSON file containing a list of Q&A entries.

            Args:
                file_path (Path): Path to the JSON file.

            Returns:
                List[TextNode]: A list of valid `TextNode` objects, or an empty list on failure.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    logger.warning(f"Invalid format in {file_path.name}, expected list of Q&A objects.")
                    return []
                return format_qa_documents(data=data, filename=file_path.name,request=self.request)
        except Exception as e:
            logger.error(f"Failed to read JSON: {file_path}, Error: {e}")
            return []

    def _load_csv(self, file_path: Path) -> List[TextNode]:
        """
        Reads and parses a CSV file containing Q&A entries.

        Args:
            file_path (Path): Path to the CSV file.

        Returns:
            List[TextNode]: A list of valid `TextNode` objects, or an empty list on failure.
        """
        try:
            with open(file_path, encoding="utf-8", newline='') as f:
                reader = csv.DictReader(f)
                if not REQUIRED_FIELDS.issubset(reader.fieldnames):
                    logger.warning(f"Missing required fields in {file_path.name}")
                    return []
                return format_qa_documents(data=reader, filename=file_path.name,request=self.request)
        except Exception as e:
            logger.error(f"Failed to read CSV: {file_path}, Error: {e}")
            return []

# --------------------------------------------------------
#                   Factory Functions
# --------------------------------------------------------

def get_qa_document_reader(request:Request) -> CustomQADirectoryReader:
    """
    Factory function to initialize and return a CustomQADirectoryReader instance.

    This reader is designed to load Q&A-style documents (from JSON or CSV files) 
    from a predefined source directory for further processing or indexing.

    Returns:
        CustomQADirectoryReader: An instance configured to read structured Q&A files
                                 from the source directory defined by `g.source_directory`.

    """
    logger.info("Initializing CustomQADirectoryReader for path: '%s'", request.state.source_directory)
    return CustomQADirectoryReader(request.state.source_directory,request)


def get_qa_input_reader(input_json: List[Dict],request:Request) -> List[TextNode]:
    """
     Converts a structured in-memory JSON list (e.g., from an API request body)
    into a list of LlamaIndex TextNode objects with custom node_ids and metadata.

    This is useful for real-time ingestion of Q&A entries from frontend or service requests
    without reading from files.

    Args:
        input_json (List[Dict]): List of Q&A entries, where each entry is a dictionary containing
                                 at least the required fields (e.g., 'id', 'question').

    Returns:
        List[TextNode]: A list of structured TextNode objects, each containing:
            - Formatted text (e.g., "Question: ...")
            - Custom node_id based on the entry's 'id'
            - Metadata including 'doc_id' and 'user_type'
    """
    logger.info(f"Processing {len(input_json)} Q&A entries from input data")
    return format_qa_documents(data=input_json,request=request)