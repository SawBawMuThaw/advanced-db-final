from pydantic import BaseModel, Field

class DonationInput(BaseModel):
    userID : int = Field(gt=0, description="ID of user making the donation")
    campaignID : str = Field(min_length=1, description="ID of campaign receiving the donation")
    amount : float = Field(gt=0, description="Amount of the donation")
    time : str = Field(min_length=1, description="Time of the donation in YY-MM-DD HH:MM:SS format")
