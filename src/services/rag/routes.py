# routes.py
import logging
from fastapi import APIRouter,HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# Import the service function that contains the core ingestion logic
from src.services.rag.rag_services import QA_RAGService
from src.services.rag.models import RAGType,RAGRequestModel



logger = logging.getLogger(__name__)

rag_router = APIRouter()

@rag_router.post("/")
async def rag_svc_main_endpoint(input_request:RAGRequestModel,request:Request):
    """
    Initializes and runs the rag service pipeline
    This function contains the core business logic.
    The a rag pipeline type is needed else defaults to question answer

    Returns:
        list[str]: Answers to each question asked
    """
    logger.info("--- Received request for RAG SVC MAIN API Endpoint ---")
    
    #-------------------------------------------------------------------#
    # """In feature we need know where user_type is correct or not?"""  #
    #-------------------------------------------------------------------#
    
    # set the user_type 
    user_type = input_request.user_type
    request.state.user_type=user_type

    try:
        rag_type = input_request.rag_type or RAGType.QUESTION_ANSWER
        logger.debug(f"rag_type from request: {rag_type}")
    except (ValueError,KeyError):
        rag_type = RAGType.QUESTION_ANSWER
        logger.warning("Invalid rag_type provided. Defaulting to QUESTION_ANSWER")

    # Initialize the RAG service 
    cur_rag_svc = QA_RAGService(rag_type=rag_type,request=request)
    logger.debug(f"QA_RAGService initialized with rag_type: {rag_type.name}")
    response = {}
    for id, question in input_request.queries.items():
        if not question.strip():
            response[id] = {
                'question': question,
                'answer': "No question provided."
            }
            continue
        response[id] = {
            'question': question,
            'answer': cur_rag_svc.get_response(question)
        }

    return JSONResponse(status_code=200,content=response)






