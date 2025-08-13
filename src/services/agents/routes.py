from fastapi import APIRouter,Depends
import logging

from src.services.agents.workflow import build_agent_graph
from src.services.agents.type import UserQueryRequest


from src.core.auth import get_cached_auth_user
from src.schemas.common_types import UserData

agent_router = APIRouter()

logger = logging.getLogger(__name__)

@agent_router.post("/")
async def process_query(input_request: UserQueryRequest, user: UserData = Depends(get_cached_auth_user)):
    state = {
        "user_query": input_request.user_query,
        "navigate_realted": None,
        "user_realted_answer": None,
        "user_answer": "",
        "is_hr_query":None,
        "metadata": input_request.metadata or {},
        "user_type":user.user_type
    }
    graph = build_agent_graph()
    final_state = graph.invoke(state)
    logger.debug(f"final_state--> {final_state}")
    if final_state['navigate_realted'] and final_state['navigation_answer']:
        return {
             "type": "action",
            "task": "redirect_url",
            "url": final_state['navigation_answer'].link,
            "data": {
                    "query_details":final_state['navigation_answer'].description,
                    "email":user.email,
                    "name":user.email.split("@")[0]
                    } 
        }
    else :
        return {
            "type": "reply",
            "message": final_state['user_answer']
            }



