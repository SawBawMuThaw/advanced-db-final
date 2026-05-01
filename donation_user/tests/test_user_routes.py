"""Tests for GET /user/{id}."""


def _register(client, username="dave", email="dave@example.com"):
    r = client.post("/register", json={"username": username,
                                        "password": "pw", "email": email})
    return r.json()["userId"]


class TestGetUser:
    def test_get_existing_user(self, client):
        uid = _register(client)
        r = client.get(f"/user/{uid}")
        assert r.status_code == 200
        assert r.json()["username"] == "dave"

    def test_get_nonexistent_user(self, client):
        r = client.get("/user/99999")
        assert r.status_code == 404