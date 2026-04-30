from pydantic import BaseModel, Field

class CommentInput(BaseModel):
    campaignId : str = Field(min_length=12)
    userId : int = Field(gt=0)
    text : str = Field(min_length=1, max_length=500)