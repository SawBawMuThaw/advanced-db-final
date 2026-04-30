from pydantic import BaseModel, Field

class ReportInput(BaseModel):
    campaignId : str = Field(min_length=12, description="ID of the campaign being reported")
    reportTitle : str = Field(min_length=1, description="Title of the report")
    amount : float = Field(gt=0, description="Amount being reported")