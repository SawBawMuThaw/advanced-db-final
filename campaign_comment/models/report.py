from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class Report(BaseModel):
    reportId : str = Field(alias="_id", default=None)
    reportTitle : str = Field(min_length=1, max_length=250)
    time : datetime = Field()
    amount : float = Field(gt=0)
    attachedImages : List[str] = Field(default=[])
    