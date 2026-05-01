from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class DonationCreate(BaseModel):
    userID: int
    campaignID: str
    amount: Decimal
    time: datetime


class DonationResponse(BaseModel):
    donationId: int


class DonorDetail(BaseModel):
    username: str
    amount: Decimal
    time: datetime


class CampaignDonationsResponse(BaseModel):
    campaignID: str
    donors: list[DonorDetail]