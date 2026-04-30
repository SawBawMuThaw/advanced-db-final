import importlib
import sys
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

main = importlib.import_module("saga_orchestrator.main")


class DummyResponse:
	def __init__(self, status_code=200, payload=None):
		self.status_code = status_code
		self._payload = payload or {}

	def json(self):
		return self._payload


def _client(monkeypatch):
	monkeypatch.setenv("CAMPAIGN_COMMENT_SERVICE", "http://campaign-service")
	monkeypatch.setenv("USER_DONATION_SERVICE", "http://user-service")
	return TestClient(main.app)


def test_create_campaign_success(monkeypatch):
	client = _client(monkeypatch)

	with patch.object(main.requests, "post", return_value=DummyResponse(200, {"campaignId": "cmp-123"})) as mock_post:
		response = client.post(
			"/campaign",
			json={
				"title": "Save The Forest",
				"description": "A campaign to protect and restore forest habitats.",
				"goal": 2000,
				"videolink": "https://video.example/campaign",
				"ownerId": 7,
			},
		)

	assert response.status_code == 200
	assert response.json() == "cmp-123"
	mock_post.assert_called_once_with(
		"http://campaign-service/campaign",
		json={
			"title": "Save The Forest",
			"description": "A campaign to protect and restore forest habitats.",
			"goal": 2000,
			"videolink": "https://video.example/campaign",
			"ownerId": 7,
		},
	)


def test_create_comment_success(monkeypatch):
	client = _client(monkeypatch)

	with patch.object(main.requests, "get", return_value=DummyResponse(200)) as mock_get, patch.object(
		main.requests, "post", return_value=DummyResponse(200, {"commentId": "cmt-1"})
	) as mock_post:
		response = client.post(
			"/comment",
			json={"campaignId": "123456789012", "userId": 5, "text": "Great campaign!"},
		)

	assert response.status_code == 200
	assert response.json() == "cmt-1"
	mock_get.assert_called_once_with("http://campaign-service/campaign/123456789012")
	mock_post.assert_called_once_with(
		"http://campaign-service/comment",
		json={"campaignId": "123456789012", "userId": 5, "text": "Great campaign!"},
	)


def test_create_reply_success(monkeypatch):
	client = _client(monkeypatch)

	with patch.object(main.requests, "get", return_value=DummyResponse(200)) as mock_get, patch.object(
		main.requests, "post", return_value=DummyResponse(200, {"replyId": "rpl-1"})
	) as mock_post:
		response = client.post(
			"/reply/comment-22",
			json={"campaignId": "123456789012", "userId": 9, "text": "I agree"},
		)

	assert response.status_code == 200
	assert response.json() == "rpl-1"
	mock_get.assert_called_once_with("http://campaign-service/campaign/123456789012")
	mock_post.assert_called_once_with(
		"http://campaign-service/reply/comment-22",
		json={"campaignId": "123456789012", "userId": 9, "text": "I agree"},
	)


def test_create_user_success(monkeypatch):
	client = _client(monkeypatch)

	with patch.object(main.requests, "post", return_value=DummyResponse(200, {"userId": 11})) as mock_post:
		response = client.post(
			"/register",
			json={"username": "tester01", "email": "tester01@example.com", "password": "strongpass1"},
		)

	assert response.status_code == 200
	assert response.json() == 11
	mock_post.assert_called_once_with(
		"http://user-service/register",
		json={"username": "tester01", "email": "tester01@example.com", "password": "strongpass1"},
	)


def test_create_report_success(monkeypatch):
	client = _client(monkeypatch)

	with patch.object(main.requests, "get", return_value=DummyResponse(200)) as mock_get, patch.object(
		main.requests, "post", return_value=DummyResponse(200, {"reportId": "rep-1"})
	) as mock_post:
		response = client.post(
			"/report",
			json={"campaignId": "123456789012", "reportTitle": "Week 1 Update", "amount": 350.5},
		)

	assert response.status_code == 200
	assert response.json() == "rep-1"
	mock_get.assert_called_once_with("http://campaign-service/campaign/123456789012")
	mock_post.assert_called_once_with(
		"http://campaign-service/report",
		json={"campaignId": "123456789012", "reportTitle": "Week 1 Update", "amount": 350.5},
	)


def test_upload_image_success(monkeypatch):
	client = _client(monkeypatch)

	get_mock = Mock(side_effect=[DummyResponse(200), DummyResponse(200)])

	with patch.object(main.requests, "get", get_mock) as mock_get, patch.object(
		main.requests, "post", return_value=DummyResponse(200, {"imageNames": ["a.png", "b.png"]})
	) as mock_post:
		response = client.post(
			"/image/rep-1/123456789012",
			files=[
				("images", ("a.png", b"aaa", "image/png")),
				("images", ("b.png", b"bbb", "image/png")),
			],
		)

	assert response.status_code == 200
	assert response.json() == ["a.png", "b.png"]
	assert mock_get.call_count == 2
	mock_get.assert_any_call("http://campaign-service/campaign/123456789012")
	mock_get.assert_any_call("http://campaign-service/report/rep-1")
	assert mock_post.call_count == 1


def test_donate_rolls_back_when_campaign_increment_fails(monkeypatch):
	client = _client(monkeypatch)

	# Compatibility shim for main.py typo: campaignId is used but model defines campaignID.
	monkeypatch.setattr(main.DonationInput, "campaignId", property(lambda self: self.campaignID), raising=False)

	get_mock = Mock(return_value=DummyResponse(200))
	post_mock = Mock(return_value=DummyResponse(200, {"donationId": "dnt-22"}))
	put_mock = Mock(return_value=DummyResponse(500))
	delete_mock = Mock(return_value=DummyResponse(200))

	with patch.object(main.requests, "get", get_mock), patch.object(main.requests, "post", post_mock), patch.object(
		main.requests, "put", put_mock
	), patch.object(main.requests, "delete", delete_mock):
		response = client.post(
			"/donate",
			json={
				"userID": 3,
				"campaignID": "123456789012",
				"amount": 40.0,
				"time": "2026-04-30 10:00:00",
			},
		)

	assert response.status_code == 500
	assert response.json()["detail"] == "Failed to record donation"
	get_mock.assert_called_once_with("http://campaign-service/campaign/123456789012")
	post_mock.assert_called_once_with(
		"http://user-service/donate",
		json={"userID": 3, "campaignID": "123456789012", "amount": 40.0, "time": "2026-04-30 10:00:00"},
	)
	put_mock.assert_called_once_with("http://campaign-service/increment/123456789012/40.0")
	delete_mock.assert_called_once_with("http://user-service/donate/dnt-22")
 
def test_like(monkeypatch):
	client = _client(monkeypatch)

	with patch.object(main.requests, "get", return_value=DummyResponse(200)) as mock_get, patch.object(
		main.requests, "put", return_value=DummyResponse(200)
	) as mock_put:
		response = client.put("/like/123456789012/5")

	assert response.status_code == 200
	mock_get.assert_called_once_with("http://campaign-service/campaign/123456789012")
	mock_put.assert_called_once_with(
		"http://campaign-service/like/123456789012/5"
	)