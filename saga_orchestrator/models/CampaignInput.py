from pydantic import BaseModel, Field

class CampaignInput(BaseModel):
    title : str = Field(min_length=1, max_length=100, description="Title of the campaign")
    description : str = Field(min_length=10, max_length=200, description="Description of the campaign")
    goal : float = Field(gt=0, description="Funding goal for the campaign")
    videolink : str = Field(min_length=5, description="Link to the campaign video")
    ownerId : int = Field(gt=0, description="ID of the user creating the campaign")
    
    