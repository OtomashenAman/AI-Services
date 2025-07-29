# qa_sql_writer.py
from src.services.ingestion.models import QAPair
from .storage_context import create_postgres_session
import logging

logger = logging.getLogger(__name__)

def insert_qa_to_postgres(question: str, answer: str, tenant_id: str, session) -> int:
    try:
        qa = QAPair(
            question=question,
            answer=answer,
            tenant_id=tenant_id,
        )
        session.add(qa)
        session.flush()        # Push to DB without committing
        session.refresh(qa)    # Retrieve auto-generated id
        logger.info(f"Prepared QAPair with id={qa.id}")
        return qa.id
    except Exception as e:
        logger.exception("Error inserting QAPair into PostgreSQL: %s", str(e))
        raise  # Let the calling function handle rollback

