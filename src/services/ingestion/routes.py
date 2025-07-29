from fastapi import APIRouter,HTTPException,Request
import logging
from fastapi.responses import JSONResponse
import os
import shutil



# file import 

from src.core.enums import IngestionType
from src.services.ingestion.pipeline import (
    run_ingestion_pipeline,
    run_question_pipeline,
    run_input_json_pipeline
)
from src.services.shared.blob_handler import AzureBlobHandler
from .settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from src.services.ingestion.utils import deleteQA,updateQA,delete_file
from src.services.ingestion.models import IngestionRequestModel,DeleteQARequestModel,UpdateQARequestModel


logger = logging.getLogger(__name__)


ingest_router = APIRouter()

@ingest_router.post("/")
async def data_ingestion_endpoint(
    request_body: IngestionRequestModel,
    request: Request):
    """
    Ingests documents based on the request type:
      - FILE_INSERT: loads and indexes local docs from S3
      - QA_FILE_INSERT: loads and indexes Q&A pairs from S3 (JSON/CSV)
      - QA_INPUT_INSERT: directly indexes Q&A JSON from API request

    Returns JSON response with processing details.
    """
    logger.info("Received request for Ingestion API Endpoint")
    source_path = None
    response_data = {
        'status': 'success',
        'documents_processed': 0,
        'processed_files': dict(),
        'message': "Ingestion ran, but no new documents were found or processed."
    }
    processed_files = dict()
    try:
        ingestion_type = request_body.type
        input_info = request_body.input_data.dict()
        metafield = request_body.input_data.metafield.dict()
        tenant_id = metafield['tenant_id']
        
        #-------------------------------------------------------------------#
        # """In feature we need know where tenant_id is correct or not?"""  #
        #-------------------------------------------------------------------#
        
        # set the tenant_id 
        request.state.tenant_id = tenant_id
        request.state.CHUNK_SIZE = CHUNK_SIZE
        request.state.CHUNK_OVERLAP = CHUNK_OVERLAP

        # ---------- TYPE-BASED ROUTING ----------
        if ingestion_type == IngestionType.QA_FILE_INSERT.name:
            blobClient = AzureBlobHandler()
            source_path = blobClient.blob_handling(input_info,request)
            processed_files = run_question_pipeline(request=request)

        elif ingestion_type == IngestionType.FILE_INSERT.name:
            if 'doc_id' not in metafield:
                raise ValueError("'doc_id' values is missing!!.")
            
            request.state.doc_id=metafield['doc_id']
            blobClient = AzureBlobHandler()
            source_path = blobClient.blob_handling(input_info,request)
            processed_files = run_ingestion_pipeline(request=request)

        elif ingestion_type == IngestionType.QA_INPUT_INSERT.name:
            if "data" not in input_info: 
                raise ValueError("'data' field missing in 'input_data' for QA_INPUT_INSERT.")
            if  not input_info['data']:
                raise ValueError("In 'data' value is missing or empty ")
            qa_list = input_info["data"]
            processed_files = run_input_json_pipeline(qa_list,request)
            
        else:
            raise ValueError(f"Unsupported ingestion type: {ingestion_type}")

        if processed_files:
            response_data.update({
                'documents_processed': len(processed_files),
                'processed_files': processed_files,
                'message': f"Ingestion successful. Processed {len(processed_files)} document(s)."
            })

    except Exception as e:
        logger.critical("Fatal error during ingestion process", exc_info=True)
        return HTTPException(
            status_code=500,
            detail=f"An error occurred during the ingestion process: {str(e)}"
        )

    finally:
        # --------- Cleanup Local Directory if Needed ----------
        try:
            if source_path:
                abs_path = os.path.abspath(source_path)
                if abs_path.startswith(os.getcwd()) and os.path.exists(abs_path):
                    shutil.rmtree(abs_path)
                    logger.info(f"Cleaned up temporary directory: {abs_path}")
                    # Check and delete parent directory if it's now empty
                    parent_dir = os.path.dirname(abs_path)
                    if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                        shutil.rmtree(parent_dir)
                        logger.info(f"Cleaned up empty parent directory: {parent_dir}")
                else:
                    logger.warning(f"Skipping cleanup. Unsafe path: {abs_path}")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}", exc_info=True)

    return JSONResponse(response_data,status_code=200)


@ingest_router.delete('/deleteQA')
async def delete_endpoint(request: DeleteQARequestModel):
    try:
        
        # Extract input_data structure
        input_data = request.input_data.dict()
        metafield = input_data.get("metafield", {})
        tenant_id = metafield.get("tenant_id")
        docs = input_data.get("data", [])

        deleted,not_deleted= await deleteQA(docs,tenant_id)

        response = {
            "summary": {
                "deleted_count": len(deleted),
                "not_deleted_count": len(not_deleted)
            },
            "deleted": deleted,
            "not_deleted": not_deleted
        }

        return JSONResponse(response,status_code=200)

    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=f"An error occurred during the deletionQA process: {str(e)}")

    
@ingest_router.put('/updateQA')
async def update_by_doc_id(request:UpdateQARequestModel):
    try:
        request_data = request.dict()
        input_data = request_data.get("input_data", {})
        metafield = input_data.get("metafield", {})
        tenant_id = metafield.get("tenant_id")
        docs = input_data.get("data", [])


        updated,not_updated= await updateQA(docs,tenant_id)

        return JSONResponse({
            "summary": {
                "updated_count": len(updated),
                "not_updated_count": len(not_updated)
            },
            "updated": updated,
            "not_updated": not_updated
        },
        status_code=200)

    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=f"An error occurred during the updateQA process: {str(e)}"
        )



@ingest_router.delete('/deletefile')
async def delete_file_endpoint(request:Request):
    """
    DELETE /deletefile
    Deletes all matching vectors from Qdrant and associated documents from PostgreSQL
    (both docstore and indexstore) for a given tenant_id and file_name.

    Request JSON:
    {
        "tenant_id": "<tenant-id>",
        "doc_id" : "<doc-id>",
        "file_name": ["<file-name>"]
    }

    Returns:
        JSON response containing:
        - Number of deleted vectors from Qdrant
        - List of deleted doc_ids
        - List of doc_ids not found in docstore or indexstore
    """
    try:
        # ---- Step 0: Parse and validate input JSON ----
        data = await request.json()
        tenant_id = data.get('tenant_id')
        file_names = data.get('file_name')

        logger.info(f"Received delete request for tenant_id='{tenant_id}', file_name='{file_names}'")

        missing_docstore,missing_indexstore,total_deleted_doc_ids =await delete_file(
            file_names=file_names,
            tenant_id= tenant_id
        )

        # ---- Step 5: Final response ----
        return JSONResponse({
            "message": f"Deleted {len(total_deleted_doc_ids)} vectors from Qdrant.",
            "deleted_doc_ids": list(set(total_deleted_doc_ids)),
            "missing_in_docstore": list(set(missing_docstore)),
            "missing_in_indexstore": list(set(missing_indexstore))
        },
        status_code=200
        )

    except Exception as e:
        return HTTPException(status_code=500,
                             detail=f"An error occurred during the delete_file process: {str(e)}"
        )
