from pydantic import BaseModel, Field
from typing import List, Optional
from .user import User

class Comment(BaseModel):
    commentId : Optional[str] = Field(alias="_id", default=None)
    user : User
    text : str
    replies : List['Comment']