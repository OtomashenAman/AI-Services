from pydantic import BaseModel
from typing import Any, Dict

class IngestionResponse(BaseModel):
    status: str
    documents_processed: int
    processed_files: Dict[str, Any]
    message: str
