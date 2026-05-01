from pydantic import BaseModel, Field

class Comment(BaseModel):
    commentId : str = Field(alias="_id")
    campaignId : str
    parentId : str | None = Field(default=None)
    user : dict
    text : str
    replies : list = Field(default=[])
