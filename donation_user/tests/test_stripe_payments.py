import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

from donation_user.services.stripe_service import StripePaymentService
from donation_user.models.donation import (
    StripePaymentIntentRequest,
    StripeConfirmPaymentRequest,
)


class TestStripePaymentService:
    """Test suite for Stripe payment service"""
    
    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_success(self, mock_create):
        """Test successful payment intent creation"""
        # Mock the Stripe response
        mock_intent = Mock()
        mock_intent.client_secret = "pi_test_secret_123"
        mock_intent.id = "pi_test_123"
        mock_create.return_value = mock_intent
        
        # Call the service
        result = StripePaymentService.create_payment_intent(
            amount=Decimal("10.50"),
            currency="usd",
            user_id=1,
            campaign_id="test_campaign_123",
            description="Test donation"
        )
        
        # Assertions
        assert result["success"] is True
        assert result["client_secret"] == "pi_test_secret_123"
        assert result["payment_intent_id"] == "pi_test_123"
        assert result["amount"] == Decimal("10.50")
        assert result["currency"] == "usd"
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["payment_method_types"] == ["card"]
    
    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_stripe_error(self, mock_create):
        """Test payment intent creation with Stripe error"""
        # Mock a Stripe error
        import stripe
        mock_create.side_effect = stripe.error.RateLimitError("Rate limited")
        
        result = StripePaymentService.create_payment_intent(
            amount=Decimal("10.50"),
            currency="usd",
        )
        
        assert result["success"] is False
        assert "Rate limited" in result["error"]
        assert result["error_type"] == "RateLimitError"
    
    @patch("stripe.PaymentIntent.retrieve")
    def test_confirm_payment_intent_success(self, mock_retrieve):
        """Test successful payment confirmation"""
        # Mock the Stripe response
        mock_intent = Mock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_intent.amount = 1050  # $10.50 in cents
        mock_intent.currency = "usd"
        mock_intent.client_secret = "pi_test_secret_123"
        mock_intent.metadata = {"user_id": "1", "campaign_id": "test_campaign"}
        mock_intent.charges = Mock()
        mock_intent.charges.data = [Mock(), Mock()]  # 2 charges
        mock_retrieve.return_value = mock_intent
        
        result = StripePaymentService.confirm_payment_intent("pi_test_123")
        
        assert result["success"] is True
        assert result["status"] == "succeeded"
        assert result["amount"] == 10.50
        assert result["charges"] == 2
    
    @patch("stripe.PaymentIntent.retrieve")
    def test_confirm_payment_intent_not_found(self, mock_retrieve):
        """Test payment confirmation with invalid intent ID"""
        import stripe
        mock_retrieve.side_effect = stripe.error.InvalidRequestError(
            "No such payment intent",
            param="id"
        )
        
        result = StripePaymentService.confirm_payment_intent("pi_invalid")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @patch("stripe.PaymentIntent.list")
    def test_list_recent_payments(self, mock_list):
        """Test listing recent payments"""
        # Mock payment intents
        mock_intent1 = Mock()
        mock_intent1.id = "pi_test_1"
        mock_intent1.status = "succeeded"
        mock_intent1.amount = 1000
        mock_intent1.currency = "usd"
        mock_intent1.created = 1234567890
        mock_intent1.metadata = {"user_id": "1"}
        
        mock_intent2 = Mock()
        mock_intent2.id = "pi_test_2"
        mock_intent2.status = "processing"
        mock_intent2.amount = 2000
        mock_intent2.currency = "usd"
        mock_intent2.created = 1234567891
        mock_intent2.metadata = {}
        
        mock_list_result = Mock()
        mock_list_result.data = [mock_intent1, mock_intent2]
        mock_list.return_value = mock_list_result
        
        result = StripePaymentService.list_recent_payments(limit=2)
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["payments"]) == 2
        assert result["payments"][0]["status"] == "succeeded"
        assert result["payments"][1]["status"] == "processing"
    
    @patch("stripe.Account.retrieve")
    def test_connection_success(self, mock_retrieve):
        """Test successful Stripe connection"""
        mock_account = Mock()
        mock_account.id = "acct_test_123"
        mock_account.email = "test@example.com"
        mock_account.country = "US"
        mock_retrieve.return_value = mock_account
        
        result = StripePaymentService.test_connection()
        
        assert result["success"] is True
        assert result["account_id"] == "acct_test_123"
        assert result["email"] == "test@example.com"
        assert result["country"] == "US"
    
    @patch("stripe.Account.retrieve")
    def test_connection_authentication_error(self, mock_retrieve):
        """Test Stripe connection with invalid API key"""
        import stripe
        mock_retrieve.side_effect = stripe.error.AuthenticationError("Invalid API key")
        
        result = StripePaymentService.test_connection()
        
        assert result["success"] is False
        assert "Invalid Stripe API key" in result["error"]


class TestStripePaymentModels:
    """Test Pydantic models for Stripe payments"""
    
    def test_payment_intent_request_model(self):
        """Test StripePaymentIntentRequest model"""
        request = StripePaymentIntentRequest(
            amount=Decimal("25.99"),
            currency="usd",
            userID=5,
            campaignID="507f1f77bcf86cd799439011",
            description="Test donation"
        )
        
        assert request.amount == Decimal("25.99")
        assert request.currency == "usd"
        assert request.userID == 5
        assert request.campaignID == "507f1f77bcf86cd799439011"
    
    def test_payment_intent_request_defaults(self):
        """Test StripePaymentIntentRequest with defaults"""
        request = StripePaymentIntentRequest(amount=Decimal("10.00"))
        
        assert request.amount == Decimal("10.00")
        assert request.currency == "usd"
        assert request.userID is None
        assert request.campaignID is None
    
    def test_confirm_payment_request_model(self):
        """Test StripeConfirmPaymentRequest model"""
        request = StripeConfirmPaymentRequest(
            payment_intent_id="pi_test_123",
            userID=5,
            campaignID="507f1f77bcf86cd799439011"
        )
        
        assert request.payment_intent_id == "pi_test_123"
        assert request.userID == 5
        assert request.campaignID == "507f1f77bcf86cd799439011"


class TestStripeIntegrationScenarios:
    """Integration tests for complete payment flows"""
    
    @patch("stripe.PaymentIntent.create")
    @patch("stripe.PaymentIntent.retrieve")
    def test_complete_payment_flow(self, mock_retrieve, mock_create):
        """Test complete payment flow: create intent -> confirm payment"""
        # Step 1: Create payment intent
        mock_create_intent = Mock()
        mock_create_intent.client_secret = "pi_secret_123"
        mock_create_intent.id = "pi_123"
        mock_create.return_value = mock_create_intent
        
        create_result = StripePaymentService.create_payment_intent(
            amount=Decimal("50.00"),
            currency="usd",
            user_id=1,
            campaign_id="campaign_123"
        )
        
        assert create_result["success"] is True
        assert create_result["payment_intent_id"] == "pi_123"
        
        # Step 2: Simulate payment and confirm
        mock_confirm_intent = Mock()
        mock_confirm_intent.id = "pi_123"
        mock_confirm_intent.status = "succeeded"
        mock_confirm_intent.amount = 5000  # $50 in cents
        mock_confirm_intent.currency = "usd"
        mock_confirm_intent.client_secret = "pi_secret_123"
        mock_confirm_intent.metadata = {}
        mock_confirm_intent.charges = Mock()
        mock_confirm_intent.charges.data = [Mock()]
        mock_retrieve.return_value = mock_confirm_intent
        
        confirm_result = StripePaymentService.confirm_payment_intent("pi_123")
        
        assert confirm_result["success"] is True
        assert confirm_result["status"] == "succeeded"
        assert confirm_result["amount"] == 50.00
    
    @patch("stripe.PaymentIntent.create")
    def test_payment_amount_conversion_cents(self, mock_create):
        """Test that payment amounts are correctly converted to cents"""
        mock_intent = Mock()
        mock_intent.client_secret = "secret"
        mock_intent.id = "pi_test"
        mock_create.return_value = mock_intent
        
        # Test various amounts
        test_amounts = [
            (Decimal("10.00"), 1000),
            (Decimal("99.99"), 9999),
            (Decimal("0.50"), 50),
            (Decimal("1000.00"), 100000),
        ]
        
        for amount, expected_cents in test_amounts:
            StripePaymentService.create_payment_intent(amount=amount)
            
            # Check that create was called with correct amount in cents
            call_args = mock_create.call_args
            assert call_args.kwargs["amount"] == expected_cents
            assert call_args.kwargs["payment_method_types"] == ["card"]


class TestStripeConfirmRoute:
    @patch("donation_user.routes.donation_routes.requests.put")
    @patch("stripe.PaymentIntent.retrieve")
    def test_confirm_payment_updates_campaign_total(self, mock_retrieve, mock_put, client, monkeypatch):
        monkeypatch.setenv("CAMPAIGN_COMMENT_SERVICE", "http://campaign-service")
        mock_put.return_value = Mock(status_code=200)

        mock_intent = Mock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_intent.amount = 2500
        mock_intent.currency = "usd"
        mock_intent.client_secret = "pi_test_secret_123"
        mock_intent.metadata = {}
        mock_intent.charges = Mock()
        mock_intent.charges.data = [Mock()]
        mock_retrieve.return_value = mock_intent

        response = client.post("/stripe/confirm-payment", json={
            "payment_intent_id": "pi_test_123",
            "userID": 1,
            "campaignID": "campaign_abc123",
        })

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["payment_status"] == "succeeded"
        donors_response = client.get("/donate/campaign_abc123")
        assert len(donors_response.json()["donors"]) == 1
        mock_put.assert_called_once_with("http://campaign-service/increment/campaign_abc123/25.0")

    @patch("donation_user.routes.donation_routes.requests.put")
    @patch("stripe.PaymentIntent.retrieve")
    def test_confirm_payment_rolls_back_when_campaign_update_fails(self, mock_retrieve, mock_put, client, monkeypatch):
        monkeypatch.setenv("CAMPAIGN_COMMENT_SERVICE", "http://campaign-service")
        mock_put.return_value = Mock(status_code=400, json=Mock(return_value={"detail": "Campaign is closed"}))

        mock_intent = Mock()
        mock_intent.id = "pi_test_456"
        mock_intent.status = "succeeded"
        mock_intent.amount = 1500
        mock_intent.currency = "usd"
        mock_intent.client_secret = "pi_test_secret_456"
        mock_intent.metadata = {}
        mock_intent.charges = Mock()
        mock_intent.charges.data = [Mock()]
        mock_retrieve.return_value = mock_intent

        response = client.post("/stripe/confirm-payment", json={
            "payment_intent_id": "pi_test_456",
            "userID": 1,
            "campaignID": "campaign_abc123",
        })

        assert response.status_code == 200
        assert response.json()["success"] is False
        assert "Campaign is closed" in response.json()["error"]
        donors_response = client.get("/donate/campaign_abc123")
        assert donors_response.json()["donors"] == []


@pytest.fixture
def stripe_config():
    """Fixture for Stripe configuration"""
    return {
        "secret_key": "sk_test_123456789",
        "publishable_key": "pk_test_123456789",
    }


@pytest.fixture
def sample_payment_data():
    """Fixture for sample payment data"""
    return {
        "amount": Decimal("25.50"),
        "currency": "usd",
        "user_id": 1,
        "campaign_id": "507f1f77bcf86cd799439011",
    }
