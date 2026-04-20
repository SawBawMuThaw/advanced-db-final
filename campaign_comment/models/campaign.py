from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .user import User
from .comment import Comment

class Info(BaseModel):
    title : str
    owner : User
    description : str
    videolink : str = Field(min_length=1, max_length=100)
    likes : int
    likedBy : List[int]
    created: datetime

class Campaign(BaseModel):
    campaignID : Optional[str] = Field(alias="_id", default=None)
    goal : float 
    current : float
    isOpen : bool = Field(default=True)
    info : Info
    comments : List[Comment]
      
    model_config = ConfigDict(populate_by_name=True)
    
