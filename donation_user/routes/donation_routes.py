from fastapi import APIRouter, HTTPException, status

from ..models.donation import (
    CampaignDonationsResponse,
    DonationCreate,
    DonationResponse,
    DonorDetail,
    RunningTotalEntry,
    RunningTotalResponse,
    StripePaymentIntentRequest,
    StripePaymentIntentResponse,
    StripeConfirmPaymentRequest,
    StripeConfirmPaymentResponse,
    StripeTestPaymentsResponse,
)
from ..repository.donation_repo import DonationRepository
from ..services.stripe_service import stripe_service


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
        result = _donations.create_donation(
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
    if not isinstance(result, dict):
        result = {"donationId": result}
    return DonationResponse(
        donationId=result["donationId"],
        receiptGenerated=bool(result.get("receiptGenerated", False)),
        receiptId=result.get("receiptId"),
        tax=result.get("tax"),
    )


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


# ==================== STRIPE PAYMENT ENDPOINTS ====================

@router.post("/stripe/payment-intent", response_model=StripePaymentIntentResponse)
def create_payment_intent(body: StripePaymentIntentRequest):
    """
    Create a Stripe payment intent for a donation.
    
    Usage:
    {
        "amount": 10.50,
        "currency": "usd",
        "userID": 1,
        "campaignID": "507f1f77bcf86cd799439011",
        "description": "Donation for campaign X"
    }
    
    Test card: 4242 4242 4242 4242, any future expiry, any CVC
    """
    result = stripe_service.create_payment_intent(
        amount=body.amount,
        currency=body.currency,
        user_id=body.userID,
        campaign_id=body.campaignID,
        description=body.description,
    )
    
    if result["success"]:
        return StripePaymentIntentResponse(
            success=True,
            client_secret=result["client_secret"],
            payment_intent_id=result["payment_intent_id"],
            amount=result["amount"],
            currency=result["currency"],
        )
    else:
        return StripePaymentIntentResponse(
            success=False,
            error=result["error"],
        )


@router.post("/stripe/confirm-payment", response_model=StripeConfirmPaymentResponse)
def confirm_payment(body: StripeConfirmPaymentRequest):
    """
    Confirm a Stripe payment and record the donation in the database.
    
    Only call this AFTER the payment has been successfully charged on Stripe.
    The payment_intent_id should have status 'succeeded'.
    
    Usage:
    {
        "payment_intent_id": "pi_1234567890",
        "userID": 1,
        "campaignID": "507f1f77bcf86cd799439011"
    }
    """
    # Check payment status first
    payment_status = stripe_service.confirm_payment_intent(body.payment_intent_id)
    
    if not payment_status["success"]:
        return StripeConfirmPaymentResponse(
            success=False,
            error=payment_status["error"],
        )
    
    # Only record donation if payment succeeded
    if payment_status["status"] != "succeeded":
        return StripeConfirmPaymentResponse(
            success=False,
            error=f"Payment status is {payment_status['status']}, expected 'succeeded'",
        )
    
    try:
        # Record the donation in the database
        from datetime import datetime
        donation_data = DonationCreate(
            userID=body.userID,
            campaignID=body.campaignID,
            amount=payment_status["amount"],
            time=datetime.now(),
        )
        
        result = _donations.create_donation(
            user_id=donation_data.userID,
            campaign_id=donation_data.campaignID,
            amount=donation_data.amount,
            time=donation_data.time,
        )
        
        donation_id = result if isinstance(result, int) else result.get("donationId")
        
        return StripeConfirmPaymentResponse(
            success=True,
            donation_id=donation_id,
            payment_status=payment_status["status"],
        )
    except Exception as e:
        return StripeConfirmPaymentResponse(
            success=False,
            error=f"Failed to record donation: {str(e)}",
        )


@router.get("/stripe/test-payments", response_model=StripeTestPaymentsResponse)
def list_test_payments(limit: int = 10):
    """
    List recent payment intents for testing/debugging.
    
    Usage: GET /stripe/test-payments?limit=20
    """
    result = stripe_service.list_recent_payments(limit=limit)
    
    if result["success"]:
        return StripeTestPaymentsResponse(
            success=True,
            count=result["count"],
            payments=result["payments"],
        )
    else:
        return StripeTestPaymentsResponse(
            success=False,
            count=0,
            error=result["error"],
        )


@router.get("/stripe/health")
def stripe_health_check():
    """
    Test Stripe connection and configuration.
    """
    result = stripe_service.test_connection()
    
    if result["success"]:
        return {
            "status": "connected",
            "account_id": result.get("account_id"),
            "email": result.get("email"),
            "country": result.get("country"),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe connection failed: {result['error']}",
        )
