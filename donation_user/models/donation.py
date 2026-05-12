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


class StripePaymentIntentRequest(BaseModel):
    """Request to create a Stripe payment intent"""
    amount: Decimal
    currency: str = "usd"
    userID: Optional[int] = None
    campaignID: Optional[str] = None
    description: Optional[str] = None


class StripePaymentIntentResponse(BaseModel):
    """Response from creating a payment intent"""
    success: bool
    client_secret: Optional[str] = None
    payment_intent_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    error: Optional[str] = None


class StripeConfirmPaymentRequest(BaseModel):
    """Request to confirm a payment and record donation"""
    payment_intent_id: str
    userID: int
    campaignID: str


class StripeConfirmPaymentResponse(BaseModel):
    """Response from confirming payment"""
    success: bool
    donation_id: Optional[int] = None
    payment_status: Optional[str] = None
    error: Optional[str] = None


class StripePaymentStatus(BaseModel):
    """Payment status information"""
    payment_intent_id: str
    status: str
    amount: Decimal
    currency: str
    metadata: dict


class StripeTestPaymentsResponse(BaseModel):
    """Response for listing test payments"""
    success: bool
    count: int
    payments: list[StripePaymentStatus] = []
    error: Optional[str] = None
