"""
TDD tests for auth endpoints.

Endpoints covered:
  POST /register  – create a new user
  POST /login     – authenticate and get JWT
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _register(client, username="alice", password="secret", email="alice@example.com"):
    return client.post("/register", json={
        "username": username,
        "password": password,
        "email": email,
    })


def _login(client, username="alice", password="secret"):
    return client.post("/login", json={
        "username": username,
        "password": password,
    })


# ===========================================================================
# POST /register
# ===========================================================================
class TestRegister:
    
    def test_register_success_returns_200(self, client: TestClient):
        r = _register(client)
        assert r.status_code == 200

    def test_register_returns_user_id(self, client: TestClient):
        r = _register(client)
        assert "userId" in r.json()

    def test_register_user_id_is_integer(self, client: TestClient):
        r = _register(client)
        assert isinstance(r.json()["userId"], int)

    def test_register_two_users_get_different_ids(self, client: TestClient):
        id1 = _register(client, username="alice", email="alice@x.com").json()["userId"]
        id2 = _register(client, username="bob",   email="bob@x.com").json()["userId"]
        assert id1 != id2

    # --- duplicate checks ---------------------------------------------------

    def test_duplicate_username_returns_409(self, client: TestClient):
        _register(client, username="alice", email="alice@x.com")
        r = _register(client, username="alice", email="other@x.com")
        assert r.status_code == 409

    def test_duplicate_email_returns_409(self, client: TestClient):
        _register(client, username="alice", email="alice@x.com")
        r = _register(client, username="bob", email="alice@x.com")
        assert r.status_code == 409

    def test_duplicate_username_error_message(self, client: TestClient):
        _register(client)
        r = _register(client)
        assert "username" in r.json()["detail"].lower()

    def test_duplicate_email_error_message(self, client: TestClient):
        _register(client, username="alice", email="alice@x.com")
        r = _register(client, username="bob", email="alice@x.com")
        assert "email" in r.json()["detail"].lower()

    # --- validation errors --------------------------------------------------

    def test_missing_username_returns_422(self, client: TestClient):
        r = client.post("/register", json={"password": "secret", "email": "x@x.com"})
        assert r.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient):
        r = client.post("/register", json={"username": "alice", "email": "x@x.com"})
        assert r.status_code == 422

    def test_missing_email_returns_422(self, client: TestClient):
        r = client.post("/register", json={"username": "alice", "password": "secret"})
        assert r.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient):
        r = client.post("/register", json={})
        assert r.status_code == 422

    def test_invalid_email_format_returns_422(self, client: TestClient):
        r = _register(client, email="not_an_email")
        assert r.status_code == 422


# ===========================================================================
# POST /login
# ===========================================================================
class TestLogin:

    # --- happy path ---------------------------------------------------------

    def test_login_success_returns_200(self, client: TestClient):
        _register(client)
        r = _login(client)
        assert r.status_code == 200

    def test_login_returns_token(self, client: TestClient):
        _register(client)
        r = _login(client)
        assert "token" in r.json()

    def test_login_token_is_string(self, client: TestClient):
        _register(client)
        r = _login(client)
        assert isinstance(r.json()["token"], str)

    def test_login_token_is_not_empty(self, client: TestClient):
        _register(client)
        r = _login(client)
        assert len(r.json()["token"]) > 0

    def test_login_returns_bearer_type(self, client: TestClient):
        _register(client)
        r = _login(client)
        assert r.json()["type"] == "Bearer"

    def test_login_token_has_three_jwt_parts(self, client: TestClient):
        """A valid JWT has exactly 3 dot-separated parts."""
        _register(client)
        token = _login(client).json()["token"]
        assert len(token.split(".")) == 3

    # --- failure cases ------------------------------------------------------

    def test_wrong_password_returns_401(self, client: TestClient):
        _register(client)
        r = _login(client, password="wrongpassword")
        assert r.status_code == 401

    def test_unknown_user_returns_401(self, client: TestClient):
        r = _login(client, username="nobody", password="x")
        assert r.status_code == 401

    def test_empty_password_returns_401(self, client: TestClient):
        _register(client)
        r = _login(client, password="")
        assert r.status_code == 401

    def test_case_sensitive_username(self, client: TestClient):
        """'Alice' and 'alice' are different users."""
        _register(client, username="alice")
        r = _login(client, username="Alice")
        assert r.status_code == 401

    # --- validation errors --------------------------------------------------

    def test_missing_username_returns_422(self, client: TestClient):
        r = client.post("/login", json={"password": "secret"})
        assert r.status_code == 422

    def test_missing_password_returns_422(self, client: TestClient):
        r = client.post("/login", json={"username": "alice"})
        assert r.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient):
        r = client.post("/login", json={})
        assert r.status_code == 422