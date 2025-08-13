from typing import  TypedDict
from pydantic import BaseModel,Field
from typing import Optional, Dict, Any


# -------------------
#  Define State Schema
# -------------------

class AgentState(TypedDict):
    user_query: str
    is_hr_query: bool
    navigate_realted: bool
    user_realted_answer: bool
    user_answer: str
    navigation_answer: dict
    user_type : str


class UserQueryRequest(BaseModel):
    user_query: str
    user_type : str = None
    navigate_realted: Optional[bool] = None
    user_realted_answer : Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class SupportTicket(BaseModel):
    description: str = Field(description="Detailed description of the issue")
    link: str = Field(description="URL to support page")


class NavigationSupportCheck(BaseModel):
    is_navigation: bool = Field(description="True if the query is about navigating or redirecting")
    is_support_ticket: bool = Field(description="True if the query is about creating a support ticket")
