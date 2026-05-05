"""Tests for POST /donate, DELETE /donate/{id}, GET /donate/{campaign_id}."""
from datetime import datetime, timezone

_CAMPAIGN = "campaign_abc123"


def _make_donation(client, user_id=1, campaign_id=_CAMPAIGN, amount="50.00"):
    return client.post("/donate", json={
        "userID": user_id,
        "campaignID": campaign_id,
        "amount": amount,
        "time": datetime.now(timezone.utc).isoformat(),
    })


class TestCreateDonation:
    def test_create_donation_success(self, client):
        r = _make_donation(client)
        assert r.status_code == 200
        assert "donationId" in r.json()
        listed = client.get(f"/donate/{_CAMPAIGN}")
        assert len(listed.json()["donors"]) == 1

    def test_create_donation_returns_id(self, client):
        r = _make_donation(client)
        assert isinstance(r.json()["donationId"], int)

    def test_large_donation_returns_receipt_metadata(self, client):
        r = _make_donation(client, amount="75.00")
        data = r.json()
        assert data["receiptGenerated"] is True
        assert isinstance(data["receiptId"], int)
        receipt = client.get(f"/donate/{data['donationId']}/receipt")
        assert receipt.status_code == 200
        assert receipt.json()["amount"] == 75.0

    def test_small_donation_has_no_receipt(self, client):
        donation_id = _make_donation(client, amount="25.00").json()["donationId"]
        receipt = client.get(f"/donate/{donation_id}/receipt")
        assert receipt.status_code == 404

    def test_create_multiple_donations(self, client):
        id1 = _make_donation(client).json()["donationId"]
        id2 = _make_donation(client, amount="25.00").json()["donationId"]
        assert id1 != id2


class TestDeleteDonation:
    def test_delete_existing(self, client):
        did = _make_donation(client).json()["donationId"]
        r = client.delete(f"/donate/{did}")
        assert r.status_code == 200
        assert r.json()["deleted"] == did

    def test_delete_nonexistent_still_200(self, client):
        # Idempotent rollback – deleting a missing row is not an error
        r = client.delete("/donate/99999")
        assert r.status_code == 200


class TestGetCampaignDonations:
    def test_empty_campaign(self, client):
        r = client.get(f"/donate/no_such_campaign")
        assert r.status_code == 200
        assert r.json()["donors"] == []

    def test_donations_listed(self, client):
        # Seed a user so username lookup works
        client.post("/register", json={"username": "eve",
                                        "password": "pw",
                                        "email": "eve@x.com"})
        _make_donation(client, user_id=1)
        _make_donation(client, user_id=1, amount="30.00")
        r = client.get(f"/donate/{_CAMPAIGN}")
        assert r.status_code == 200
        assert len(r.json()["donors"]) == 2
