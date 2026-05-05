from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DonationCreate(BaseModel):
    userID: int
    campaignID: str
    amount: Decimal
    time: datetime


class DonationResponse(BaseModel):
    donationId: int
    receiptGenerated: bool = False
    receiptId: Optional[int] = None
    tax: Optional[Decimal] = None


class DonorDetail(BaseModel):
    username: str
    amount: Decimal
    time: datetime


class CampaignDonationsResponse(BaseModel):
    campaignID: str
    donors: list[DonorDetail]
    
class RunningTotalEntry(BaseModel):
    donationId: int
    username: str
    amount: float
    time: datetime
    runningTotal: float

class RunningTotalResponse(BaseModel):
    campaignID: str
    entries: list[RunningTotalEntry]
