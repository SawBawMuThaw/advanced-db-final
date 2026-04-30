"""
tests/__init__.py  –  in-memory store + monkeypatched repositories.
Imported by conftest.py and individual test modules.
"""
from __future__ import annotations
from itertools import count
from unittest.mock import patch

from auth.hashing import hash_password


class _Seq:
    def __init__(self):
        self._c = count(1)
        self._val = 1

    def next(self):
        self._val = next(self._c)
        return self._val

    def reset(self):
        self._c = count(1)
        self._val = 1


class _Store:
    users: dict[int, dict] = {}
    donations: dict[int, dict] = {}
    user_id_seq = _Seq()
    donation_id_seq = _Seq()


_store = _Store()


# ---------------------------------------------------------------------------
# Mock UserRepository
# ---------------------------------------------------------------------------
class _MockUserRepo:
    def create_user(self, username, hashed_password, email):
        uid = _store.user_id_seq.next()
        _store.users[uid] = dict(userId=uid, username=username,
                                  password=hashed_password, email=email, role="user")
        return uid

    def get_by_id(self, user_id):
        return _store.users.get(user_id)

    def get_by_username(self, username):
        return next((u for u in _store.users.values() if u["username"] == username), None)

    def username_exists(self, username):
        return any(u["username"] == username for u in _store.users.values())

    def email_exists(self, email):
        return any(u["email"] == email for u in _store.users.values())


# ---------------------------------------------------------------------------
# Mock DonationRepository
# ---------------------------------------------------------------------------
class _MockDonationRepo:
    def create_donation(self, user_id, campaign_id, amount, time):
        did = _store.donation_id_seq.next()
        _store.donations[did] = dict(donationId=did, userId=user_id,
                                      campaignId=campaign_id, amount=amount, time=time)
        return did

    def delete_donation(self, donation_id):
        _store.donations.pop(donation_id, None)

    def get_by_campaign(self, campaign_id):
        uid_to_name = {u["userId"]: u["username"] for u in _store.users.values()}
        return [
            dict(username=uid_to_name.get(d["userId"], "unknown"),
                 amount=d["amount"], time=d["time"])
            for d in _store.donations.values()
            if d["campaignId"] == campaign_id
        ]

    def get_by_id(self, donation_id):
        return _store.donations.get(donation_id)


# ---------------------------------------------------------------------------
# Activate patches for the entire test session
# ---------------------------------------------------------------------------
patch("routes.auth_routes._users",     _MockUserRepo()).start()
patch("routes.user_routes._users",     _MockUserRepo()).start()
patch("routes.donation_routes._donations", _MockDonationRepo()).start()