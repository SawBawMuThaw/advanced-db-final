from pydantic import BaseModel, Field
from typing import List
from .user import User

class Comment(BaseModel):
    commentId : str = Field(alias="_id")
    user : User
    text : str
    replies : List['Comment']