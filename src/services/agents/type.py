from typing import  TypedDict
from pydantic import BaseModel
from typing import Optional, Dict, Any
# -------------------
#  Define State Schema
# -------------------

class Agentstate(TypedDict):
    user_query: str
    navigate_realted: bool
    user_realted_answer: bool
    user_answer: str



class UserQueryRequest(BaseModel):
    user_query: str
    metadata: Optional[Dict[str, Any]] = None