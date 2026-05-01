from fastapi import APIRouter, HTTPException, status

from ..models.donation import (
    CampaignDonationsResponse,
    DonationCreate,
    DonationResponse,
    DonorDetail,
)
from ..repository.donation_repo import DonationRepository

router = APIRouter(tags=["donations"])
_donations = DonationRepository()


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
    return DonationResponse(donationId=donation_id)


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
    """
    Return all donors and their net amounts for a given campaign.
    campaign_id is a MongoDB ObjectId hex string e.g. "6630f3e2a1b2c3d4e5f60001".
    """
    donors = _donations.get_by_campaign(campaign_id)
    return CampaignDonationsResponse(
        campaignID=campaign_id,
        donors=[DonorDetail(**d) for d in donors],
    )