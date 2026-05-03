from fastapi import APIRouter, HTTPException, status

from ..models.donation import (
    CampaignDonationsResponse,
    DonationCreate,
    DonationResponse,
    DonorDetail,
    RunningTotalEntry,
    RunningTotalResponse,
)
from ..repository.donation_repo import DonationRepository


router = APIRouter(tags=["donations"])
_donations = DonationRepository()


@router.get("/donate/{campaign_id}/running-total", response_model=RunningTotalResponse)
def get_running_total(campaign_id: str):
    """
    Returns all donations for a campaign with a running total column,
    calculated using SQL window functions (SUM OVER PARTITION BY).
    """
    try:
        entries = _donations.get_running_total(campaign_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch running total: {exc}",
        )

    return RunningTotalResponse(
        campaignID=campaign_id,
        entries=[RunningTotalEntry(**e) for e in entries],
    )

@router.post("/donate", response_model=DonationResponse, status_code=200)
def create_donation(body: DonationCreate):
    """
    Record a donation against a MongoDB campaignID (ObjectId as hex string).
    The SQL trigger automatically creates the corresponding Receipt.
    Called by the Saga Orchestrator after campaign counter is incremented.
    """
    try:
        donation_id = _donations.create_donation(
            user_id=body.userID,
            campaign_id=body.campaignID,   
            amount=body.amount,
            time=body.time,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not record donation: {exc}",
        )
        
    result = _donations.create_donation(
    user_id=body.userID,
    campaign_id=body.campaignID,
    amount=body.amount,
    time=body.time,
)
    
    return DonationResponse(donationId=result["donationId"])


# NOTE: This DELETE must be defined BEFORE GET /donate/{campaign_id}
@router.delete("/donate/{donation_id}", status_code=200)
def delete_donation(donation_id: int):
    """
    Saga rollback – removes a donation.
    donation_id is a SQL integer, NOT a MongoDB ObjectId.
    """
    try:
        _donations.delete_donation(donation_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {exc}",
        )
    return {"deleted": donation_id}


@router.get("/donate/{campaign_id}", response_model=CampaignDonationsResponse)
def get_campaign_donations(campaign_id: str):
    donors = _donations.get_by_campaign(campaign_id)
    return CampaignDonationsResponse(
        campaignID=campaign_id,
        donors=[DonorDetail(**d) for d in donors],
    )
    
@router.get("/donate/{donation_id}/receipt")
def get_receipt(donation_id: int):
    receipt = _donations.get_receipt_by_donation(donation_id)
    if receipt is None:
        raise HTTPException(
            status_code=404,
            detail=f"No receipt for donation {donation_id} (amount may be under $50)"
        )
    return receipt