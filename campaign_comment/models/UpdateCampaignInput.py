from pydantic import BaseModel, Field
from typing import Optional

class UpdateCampaignInput(BaseModel):
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    close: Optional[bool] = Field(default=None)
    videolink: Optional[str] = Field(default=None)