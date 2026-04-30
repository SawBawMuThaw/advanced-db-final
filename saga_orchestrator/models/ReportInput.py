from pydantic import BaseModel, Field

class ReportInput(BaseModel):
    campaignId : str = Field(min_length=12, description="The ID of the campaign being reported")
    reportTitle : str = Field(min_length=5, description="The title of the report")
    amount : float = Field(gt=0, description="The amount being reported")