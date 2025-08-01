from typing import Optional
from pydantic import BaseModel
from uuid import UUID



class UserData(BaseModel):
    is_authenticated: bool = True
    id: Optional[UUID]
    username: Optional[str] = None
    email: Optional[str] = None
