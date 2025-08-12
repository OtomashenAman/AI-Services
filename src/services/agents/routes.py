from fastapi import APIRouter
import logging

from src.services.agents.workflow import graph
from src.services.agents.type import UserQueryRequest

agent_router = APIRouter()

logger = logging.getLogger(__name__)

@agent_router.post("/")
async def process_query(input_request: UserQueryRequest):
    state = {
        "user_query": input_request.user_query,
        "navigate_realted": False,
        "user_realted_answer": None,
        "metadata": input_request.metadata or {}
    }
    logger.info(f"-----state---> {state}")
    final_state = graph.invoke(state)
    return final_state
