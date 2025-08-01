# qa_sql_writer.py
from src.services.ingestion.models import QAPair
import logging
from typing import  List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def insert_qa_to_postgres(question: str, answer: str, user_type: str,EOR_id:str,client_id:str,contrator_id:str, session) -> int:
    try:
        qa = QAPair(
            question=question,
            answer=answer,
            user_type=user_type,
            EOR_id=EOR_id,
            client_id=client_id,
            contrator_id= contrator_id

        )
        session.add(qa)
        session.flush()        # Push to DB without committing
        session.refresh(qa)    # Retrieve auto-generated id
        logger.info(f"Prepared QAPair with id={qa.id}")
        return qa.id
    except Exception as e:
        logger.exception("Error inserting QAPair into PostgreSQL: %s", str(e))
        raise  # Let the calling function handle rollback



def delete_qa_pairs_by_ids(ids: List[int], session: Session):
    session.query(QAPair).filter(QAPair.id.in_(ids)).delete(synchronize_session=False)
