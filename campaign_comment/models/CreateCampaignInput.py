from pydantic import BaseModel, Field
from typing import Optional

class CreateCampaignInput(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=10, max_length=200)
    goal: float = Field(gt=0)
    videolink: str = Field(min_length=5)
    ownerId: int = Field(gt=0)