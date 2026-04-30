"""
conftest.py  –  shared fixtures + in-memory mocks for all donation_user tests.
No live SQL Server needed.
"""
from __future__ import annotations

from itertools import count
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ===========================================================================
# In-memory store
# ===========================================================================
class _Seq:
    def __init__(self):
        self._c = count(1)

    def next(self) -> int:
        return next(self._c)

    def reset(self):
        self._c = count(1)


class _Store:
    def __init__(self):
        self.users: dict[int, dict] = {}
        self.donations: dict[int, dict] = {}
        self.user_id_seq = _Seq()
        self.donation_id_seq = _Seq()

    def clear(self):
        self.users.clear()
        self.donations.clear()
        self.user_id_seq.reset()
        self.donation_id_seq.reset()


store = _Store()


# ===========================================================================
# Mock repositories
# ===========================================================================
class _MockUserRepo:
    def create_user(self, username, hashed_password, email):
        uid = store.user_id_seq.next()
        store.users[uid] = dict(
            userId=uid, username=username,
            password=hashed_password, email=email, role="user"
        )
        return uid

    def get_by_id(self, user_id):
        return store.users.get(user_id)

    def get_by_username(self, username):
        return next((u for u in store.users.values() if u["username"] == username), None)

    def username_exists(self, username):
        return any(u["username"] == username for u in store.users.values())

    def email_exists(self, email):
        return any(u["email"] == email for u in store.users.values())


class _MockDonationRepo:
    def create_donation(self, user_id, campaign_id, amount, time):
        did = store.donation_id_seq.next()
        store.donations[did] = dict(
            donationId=did, userId=user_id,
            campaignId=campaign_id, amount=amount, time=time
        )
        return did

    def delete_donation(self, donation_id):
        store.donations.pop(donation_id, None)

    def get_by_campaign(self, campaign_id):
        uid_to_name = {u["userId"]: u["username"] for u in store.users.values()}
        return [
            dict(username=uid_to_name.get(d["userId"], "unknown"),
                 amount=d["amount"], time=d["time"])
            for d in store.donations.values()
            if d["campaignId"] == campaign_id
        ]

    def get_by_id(self, donation_id):
        return store.donations.get(donation_id)


# ===========================================================================
# Activate patches once for the whole session
# ===========================================================================
_mock_user_repo     = _MockUserRepo()
_mock_donation_repo = _MockDonationRepo()

patch("routes.auth_routes._users",        _mock_user_repo).start()
patch("routes.user_routes._users",        _mock_user_repo).start()
patch("routes.donation_routes._donations", _mock_donation_repo).start()


# ===========================================================================
# Fixtures
# ===========================================================================
@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_store():
    """Wipe in-memory state before every single test."""
    store.clear()
    yield