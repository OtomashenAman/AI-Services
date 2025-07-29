from qdrant_client.http.models import Filter, FieldCondition, MatchValue,PointStruct
from qdrant_client.models import FilterSelector,UpdateStatus
import json
import logging
from fastapi import HTTPException



from src.services.shared.data_base.settings import QDRANT_QCOLLECTION_NAME,QDRANT_COLLECTION_NAME
from src.services.shared.data_base.storage_context import connect_qdrantDB,connect_postgres,connect_postgres_index,create_postgres_session
from src.services.ingestion.embedding_provider import get_embedding_model
from src.services.ingestion.models import QAPair

logger = logging.getLogger(__name__)

async def deleteQA(docs:list, tenant_id:str):
    client = connect_qdrantDB()
    db_session = create_postgres_session()
    deleted = []
    not_deleted = []

    for item in docs:
        doc_id = item.get("id")
        if not doc_id:
            not_deleted.append({"id": None, "reason": "Missing 'id' in data item"})
            continue

        try:
            # Step 1: Backup Qdrant point
            filter_condition = Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
                ]
            )

            scroll_result = client.scroll(
                collection_name=QDRANT_QCOLLECTION_NAME,
                scroll_filter=filter_condition,
                limit=1
            )

            points = scroll_result[0]
            if not points:
                not_deleted.append({"id": doc_id, "reason": "Qdrant point not found"})
                continue

            backup_point = points[0]  # Save for rollback if needed

            # Step 2: Delete from Qdrant
            result = client.delete(
                collection_name=QDRANT_QCOLLECTION_NAME,
                points_selector=FilterSelector(filter=filter_condition),

            )

            if result.status not in (UpdateStatus.ACKNOWLEDGED, UpdateStatus.COMPLETED):
                not_deleted.append({"id": doc_id, "reason": f"Qdrant delete not acknowledged: {result}"})
                continue

            # Step 3: Delete from PostgreSQL
            try:
                rows_deleted = db_session.query(QAPair).filter_by(id= doc_id,tenant_id=tenant_id).delete()
                if rows_deleted == 0:
                    raise Exception("No matching row in PostgreSQL")
                
                db_session.commit()
                deleted.append({"id": doc_id})
            except Exception as pg_err:
                db_session.rollback()

                try:
                    rollback_point = PointStruct(
                        id = backup_point.id,
                        vector = backup_point.vector,
                        payload= backup_point.payload
                    )
                    client.upsert(
                        collection_name=QDRANT_QCOLLECTION_NAME,
                        points=[rollback_point]
                    )
                    not_deleted.append({
                        "id": doc_id,
                        "reason":f"PostgreSQL delete failed and Qdrant restored: {pg_err}"
                    })
                except Exception as rollback_err:
                    not_deleted.append({
                        "id": doc_id,
                        "reason": f"PostgreSQL delete failed: {pg_err}; Qdrant rollback also failed: {rollback_err}"
                    })
        except Exception as delete_error:
            not_deleted.append({"id": doc_id, "reason": str(delete_error)})
    return deleted,not_deleted

async def updateQA(docs: list, tenant_id: str):
    client = connect_qdrantDB()
    embed_model = get_embedding_model()
    db_session = create_postgres_session()

    updated = []
    not_updated = []

    for item in docs:
        doc_id = item.get("id")
        question = item.get("question")

        if not doc_id or not question:
            not_updated.append({
                "id": doc_id or None,
                "reason": "Missing 'id' or 'question' in item"
            })
            continue

        try:
            # Step 1: Fetch and backup original Qdrant point
            filter_condition = Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
                ]
            )

            scroll_result = client.scroll(
                collection_name=QDRANT_QCOLLECTION_NAME,
                scroll_filter=filter_condition,
                limit=1
            )

            points = scroll_result[0]
            if not points:
                not_updated.append({"id": doc_id, "reason": "No Qdrant point found"})
                continue

            point = points[0]
            point_id = point.id
            old_payload = point.payload or {}
            old_vector = point.vector  # backup for rollback

            # Step 2: Construct new vector & payload
            new_embedding = embed_model._get_text_embedding(question)
            updated_payload = old_payload.copy()

            try:
                node_data = json.loads(old_payload.get('_node_content', '{}'))
                node_data['text'] = f"Question:{question}"
                updated_payload['_node_content'] = json.dumps(node_data)
            except Exception:
                updated_payload['_node_content'] = question

            # Step 3: Update Qdrant
            updated_point = PointStruct(
                id=point_id,
                vector=new_embedding,
                payload=updated_payload
            )

            client.upsert(
                collection_name=QDRANT_QCOLLECTION_NAME,
                points=[updated_point]
            )

            # Step 4: Update PostgreSQL
            try:
                qa_obj = db_session.query(QAPair).filter_by(id=doc_id, tenant_id=tenant_id).first()
                if qa_obj:
                    qa_obj.question = question
                    db_session.commit()
                    updated.append({"id": doc_id})
                else:
                    raise Exception("PostgreSQL record not found")

            except Exception as pg_err:
                db_session.rollback()

                # Step 5: Rollback Qdrant update
                try:
                    rollback_point = PointStruct(
                        id=point_id,
                        vector=old_vector,
                        payload=old_payload
                    )
                    client.upsert(
                        collection_name=QDRANT_QCOLLECTION_NAME,
                        points=[rollback_point]
                    )
                    not_updated.append({
                        "id": doc_id,
                        "reason": f"PostgreSQL update failed and Qdrant rollback done: {pg_err}"
                    })
                except Exception as rollback_err:
                    not_updated.append({
                        "id": doc_id,
                        "reason": f"PostgreSQL update failed: {pg_err}; Qdrant rollback also failed: {rollback_err}"
                    })

        except Exception as update_error:
            not_updated.append({"id": doc_id, "reason": str(update_error)})

    return updated, not_updated



async def delete_file(file_names:list,tenant_id:str):
    # ---- Step 1: Connect to Qdrant and PostgreSQL ----
    qdrant_client = connect_qdrantDB()
    docstore = connect_postgres()
    indexstore = connect_postgres_index()

    total_deleted_doc_ids = []
    missing_docstore = []
    missing_indexstore = []

    for file_name in file_names:
        qdrant_filter = Filter(
            must=[
                FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
                FieldCondition(key="filename", match=MatchValue(value=file_name))
            ]
        )

        # ---- Step 2: Retrieve all matching vectors ----
        deleted_doc_ids = []
        next_page_offset = None
        batch_limit = 100

        while True:
            scroll_result = qdrant_client.scroll(
                collection_name=QDRANT_COLLECTION_NAME,
                scroll_filter=qdrant_filter,
                with_payload=True,
                limit=batch_limit,
                offset=next_page_offset
            )

            points, next_page_offset = scroll_result

            if not points:
                break

            for point in points:
                payload = point.payload or {}
                doc_id = payload.get("doc_id")
                if doc_id:
                    deleted_doc_ids.append(str(doc_id))

            if next_page_offset is None:
                break

        if not deleted_doc_ids:
            logger.info(f"No vectors found for tenant_id='{tenant_id}', file_name='{file_name}'")
            continue  # Try next file

        # ---- Step 3: Delete vectors from Qdrant ----
        qdrant_client.delete(
            collection_name=QDRANT_COLLECTION_NAME,
            points_selector=FilterSelector(filter=qdrant_filter)
        )
        logger.info(f"Deleted {len(deleted_doc_ids)} vectors from Qdrant for file='{file_name}'.")

        # ---- Step 4: Delete from docstore and indexstore ----
        for doc_id in deleted_doc_ids:
            try:
                if docstore.get_document(doc_id):
                    docstore.delete_document(doc_id)
                else:
                    missing_docstore.append(doc_id)
            except Exception as e:
                logger.warning(f"Error deleting from docstore for doc_id={doc_id}: {e}")
                missing_docstore.append(doc_id)

            try:
                if indexstore.get_index_struct(doc_id):
                    indexstore.delete_index_struct(doc_id)
                else:
                    missing_indexstore.append(doc_id)
            except Exception as e:
                logger.warning(f"Error deleting from indexstore for doc_id={doc_id}: {e}")
                missing_indexstore.append(doc_id)

        total_deleted_doc_ids.extend(deleted_doc_ids)

    if not total_deleted_doc_ids:
        raise  HTTPException(
            status_code=404,
            detail="No matching documents found in Qdrant for any file."
        )
    
    return missing_docstore,missing_indexstore,total_deleted_doc_ids