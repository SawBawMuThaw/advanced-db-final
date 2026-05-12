import stripe
from decimal import Decimal
from typing import Optional, Dict, Any
from ..config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service for handling Stripe payment operations"""
    
    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = "usd",
        user_id: int = None,
        campaign_id: str = None,
        description: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent for the given amount.
        Amount should be in cents (e.g., $10.00 = 1000)
        """
        try:
            amount_cents = int(amount * 100)
            
            payment_metadata = {
                "user_id": str(user_id) if user_id else "unknown",
                "campaign_id": str(campaign_id) if campaign_id else "unknown",
            }
            if metadata:
                payment_metadata.update(metadata)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                # The frontend only collects card details with Stripe Elements.
                # Restrict the intent to cards so Stripe does not require a
                # return_url for redirect-based payment methods enabled in the dashboard.
                payment_method_types=["card"],
                description=description or f"Donation for campaign {campaign_id}",
                metadata=payment_metadata,
            )
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount,
                "currency": currency,
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm the status of a payment intent.
        Returns payment details and status.
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            charges_count = 0
            charges = getattr(intent, "charges", None)
            if charges is not None and hasattr(charges, "data"):
                charges_count = len(charges.data)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,  # Convert from cents
                "currency": intent.currency,
                "client_secret": intent.client_secret,
                "metadata": intent.metadata or {},
                "charges": charges_count,
                "latest_charge": getattr(intent, "latest_charge", None),
            }
        except stripe.error.InvalidRequestError:
            return {
                "success": False,
                "error": f"Payment intent {payment_intent_id} not found",
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def list_recent_payments(limit: int = 10) -> Dict[str, Any]:
        """
        List recent payment intents for debugging/testing
        """
        try:
            intents = stripe.PaymentIntent.list(limit=limit)
            
            payments = []
            for intent in intents.data:
                payments.append({
                    "payment_intent_id": intent.id,
                    "status": intent.status,
                    "amount": intent.amount / 100,
                    "currency": intent.currency,
                    "created": intent.created,
                    "metadata": intent.metadata or {},
                })
            
            return {
                "success": True,
                "count": len(payments),
                "payments": payments,
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def test_connection() -> Dict[str, Any]:
        """
        Test if Stripe connection is working
        """
        try:
            account = stripe.Account.retrieve()
            return {
                "success": True,
                "account_id": account.id,
                "email": account.email,
                "country": account.country,
            }
        except stripe.error.AuthenticationError:
            return {
                "success": False,
                "error": "Invalid Stripe API key",
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
            }


stripe_service = StripePaymentService()
