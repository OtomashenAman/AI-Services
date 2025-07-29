from enum import Enum, auto

class IngestionType(Enum):
    """Defines the types of update ingestion pipeline configurations available."""
    QA_FILE_INSERT = auto()
    FILE_INSERT = auto()
    QA_INPUT_INSERT = auto()

