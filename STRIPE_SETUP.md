# Stripe Payment Integration Guide

## Overview
This guide walks through setting up and testing Stripe payment integration for the donation platform.

---

## Step 1: Get Stripe API Keys

1. Go to https://dashboard.stripe.com/apikeys
2. Sign in with your Stripe account (or create one at https://dashboard.stripe.com/register)
3. You'll see two keys:
   - **Secret Key** (starts with `sk_test_` or `sk_live_`)
   - **Publishable Key** (starts with `pk_test_` or `pk_live_`)
4. Copy both keys

---

## Step 2: Configure Environment Variables

### Option A: Using existing .env file
The `.env` file already exists in `donation_user/`. Add these lines:

```env
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_test_your_webhook_secret_here
```

### Option B: Using .env.example template
```bash
cp donation_user/.env.example donation_user/.env
# Then edit donation_user/.env and add your Stripe keys
```

---

## Step 3: Install Dependencies

```bash
cd donation_user
pip install stripe python-dotenv
# Or reinstall from requirements.txt:
pip install -r requirements.txt
```

---

## Step 4: Test Stripe Connection

### Health Check Endpoint
Test if Stripe is properly configured:

```bash
# Start the server
uvicorn donation_user.main:app --reload

# In another terminal, test the health check:
curl http://localhost:8000/stripe/health
```

**Expected response (success):**
```json
{
  "status": "connected",
  "account_id": "acct_xxx",
  "email": "your@email.com",
  "country": "US"
}
```

**Error response (invalid key):**
```json
{
  "detail": "Stripe connection failed: Invalid API key"
}
```

---

## Step 5: Run Automated Tests

```bash
# Run all Stripe payment tests
pytest tests/test_stripe_payments.py -v

# Run specific test
pytest tests/test_stripe_payments.py::TestStripePaymentService::test_create_payment_intent_success -v

# Run with coverage
pytest tests/test_stripe_payments.py --cov=donation_user.services.stripe_service
```

**Test categories:**
- `TestStripePaymentService` - Core payment operations
- `TestStripePaymentModels` - Pydantic model validation
- `TestStripeIntegrationScenarios` - Complete payment flows

---

## Step 6: Manual Testing with API

### Test Cards
Stripe provides test cards for different scenarios:

| Card Number | Scenario | Expiry | CVC |
|---|---|---|---|
| `4242 4242 4242 4242` | Success | Any future (e.g., 12/25) | Any 3 digits (e.g., 123) |
| `4000 0000 0000 0002` | Declined (insufficient funds) | Any future | Any 3 digits |
| `4000 0000 0000 0069` | Expired card | 12/20 | Any 3 digits |
| `4000 0000 0000 0127` | Incorrect CVC | Any future | 99 |

### A. Create a Payment Intent

```bash
curl -X POST http://localhost:8000/stripe/payment-intent \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 25.50,
    "currency": "usd",
    "userID": 1,
    "campaignID": "507f1f77bcf86cd799439011",
    "description": "Test donation"
  }'
```

**Response:**
```json
{
  "success": true,
  "client_secret": "pi_xxx_secret_xxx",
  "payment_intent_id": "pi_xxx",
  "amount": 25.50,
  "currency": "usd"
}
```

### B. Simulate Payment in Stripe Dashboard

1. Go to https://dashboard.stripe.com/test/payments
2. You'll see the payment intent you just created
3. Click on it and complete the payment using test card `4242 4242 4242 4242`

### C. Confirm Payment and Record Donation

After the payment succeeds in Stripe, confirm it to record in database:

```bash
curl -X POST http://localhost:8000/stripe/confirm-payment \
  -H "Content-Type: application/json" \
  -d '{
    "payment_intent_id": "pi_xxx",
    "userID": 1,
    "campaignID": "507f1f77bcf86cd799439011"
  }'
```

**Response:**
```json
{
  "success": true,
  "donation_id": 42,
  "payment_status": "succeeded"
}
```

### D. List Recent Payments

```bash
curl http://localhost:8000/stripe/test-payments?limit=10
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "payments": [
    {
      "payment_intent_id": "pi_xxx",
      "status": "succeeded",
      "amount": 25.50,
      "currency": "usd",
      "metadata": {
        "user_id": "1",
        "campaign_id": "507f1f77bcf86cd799439011"
      }
    }
  ]
}
```

---

## Step 7: Frontend Integration (JavaScript)

### Install Stripe.js
```html
<script src="https://js.stripe.com/v3/"></script>
```

### Example Payment Flow

```javascript
// 1. Create payment intent on backend
const response = await fetch('http://localhost:8000/stripe/payment-intent', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    amount: 25.50,
    userID: 1,
    campaignID: 'campaign_id_here'
  })
});

const { client_secret, payment_intent_id } = await response.json();

// 2. Initialize Stripe
const stripe = Stripe('pk_test_your_publishable_key');
const elements = stripe.elements();
const cardElement = elements.create('card');
cardElement.mount('#card-element');

// 3. Handle payment
const result = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: cardElement,
    billing_details: { name: 'Jenny Rosen' }
  }
});

if (result.paymentIntent.status === 'succeeded') {
  // 4. Confirm on backend
  await fetch('http://localhost:8000/stripe/confirm-payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      payment_intent_id: payment_intent_id,
      userID: 1,
      campaignID: 'campaign_id_here'
    })
  });
  
  console.log('Donation recorded!');
}
```

---

## Step 8: Setup Stripe Webhooks (Optional)

Webhooks allow Stripe to notify your server of payment events.

### Using Stripe CLI (Recommended for local testing)

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login:
   ```bash
   stripe login
   ```
3. Forward events to your local server:
   ```bash
   stripe listen --forward-to localhost:8000/stripe/webhook
   ```
4. Add webhook endpoint to your code (if not already added)

---

## File Structure

```
donation_user/
├── config.py                      # Configuration (new)
├── services/
│   ├── __init__.py
│   └── stripe_service.py          # Stripe payment logic (new)
├── models/
│   └── donation.py                # Includes Stripe models (updated)
├── routes/
│   └── donation_routes.py          # Includes Stripe endpoints (updated)
├── tests/
│   └── test_stripe_payments.py    # Test suite (new)
├── .env                           # Environment variables (update with keys)
└── .env.example                   # Template (new)
```

---

## API Endpoints Summary

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/stripe/payment-intent` | Create a payment intent |
| `POST` | `/stripe/confirm-payment` | Confirm payment and record donation |
| `GET` | `/stripe/test-payments` | List recent test payments |
| `GET` | `/stripe/health` | Test Stripe connection |

---

## Troubleshooting

### Issue: "Invalid Stripe API key"
- **Solution**: Check `.env` file has correct `STRIPE_SECRET_KEY` from Stripe dashboard

### Issue: "Payment intent not found"
- **Solution**: Make sure payment was actually created. Check Stripe dashboard

### Issue: "Payment status is processing"
- **Solution**: Wait a moment for payment to complete, then try again

### Issue: Tests failing with mock errors
- **Solution**: Run `pip install pytest-mock` and ensure pytest is up to date

### Issue: Import errors for stripe
- **Solution**: Run `pip install stripe==11.0.0` and `pip install -r requirements.txt`

---

## Next Steps

1. ✅ Configure Stripe keys
2. ✅ Install dependencies
3. ✅ Test connection
4. ✅ Run automated tests
5. ✅ Manual API testing
6. ⏭️ Frontend integration
7. ⏭️ Webhook setup
8. ⏭️ Production deployment

---

## Support

- Stripe API Docs: https://stripe.com/docs/api
- Stripe Testing Guide: https://stripe.com/docs/testing
- Stripe Dashboard: https://dashboard.stripe.com

