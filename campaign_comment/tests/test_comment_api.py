import pytest
from testcontainers.mongodb import MongoDbContainer
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from fastapi.testclient import TestClient
from ..main import app, get_mongo_client
import requests
from ..repository.campaignRepository import get_campaign

campaign_id = "6622f0b7a12c4d91f9b00001"


@pytest.fixture(scope="session")
def mongo_container():
    with MongoDbContainer("mongo:latest") as mongo:
        yield mongo


@pytest.fixture(scope="function")
def mock_mongo_client(mongo_container, request):
    client = MongoClient(mongo_container.get_connection_url())
    db = client['charitydb']

    if 'campaigns' not in db.list_collection_names():
        db.create_collection('campaigns')

    docs = db.campaigns.find({})

    if len(list(docs)) == 0:
        doc = {
            "_id": ObjectId(campaign_id),
            "info" : {
                "title": "Save the Rainforest",
                "description": "Help us protect the rainforest and its biodiversity.",
                "videolink": "https://example.com/rainforest-video",
                "owner" : {
                    "userId": 5,
                    "username": "testuser"
                },
                "created": datetime.now(),
                'likes' : 10,
                'likedBy' : [1, 2, 3, 4, 5],
            },
            "goal": 10000.0,
            "current": 5000.0,
            "close": False,
            "reports": []
        }
        db.campaigns.insert_one(doc)
        comment = {
            "_id": ObjectId("6622f0b7a12c4d91f9b00002"),
            "userId": 10,
            "text": "Great initiative! Happy to support.",
            "campaignId": ObjectId(campaign_id),
            "parentId": None,
        }
        db.comments.insert_one(comment)
    request.addfinalizer(lambda: client.close())
    return client


class MockUserResponse:
    def __init__(self):
        self.status_code = 200

    @staticmethod
    def json():
        return {"username": "John Doe"}


test_client = TestClient(app)


def test_post_comment(mock_mongo_client, monkeypatch):
    monkeypatch.setenv("DB_NAME", "charitydb")
    monkeypatch.setenv("MONGO_URI", mock_mongo_client.address)
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client

    def mock_get(*args, **kwargs):
        return MockUserResponse()

    monkeypatch.setattr(requests, 'get', mock_get)

    payload = {
        'userId': 11,
        'text': "This is a test comment.",
        'campaignId': campaign_id
    }

    result = test_client.post("/comment", json=payload)

    assert result.status_code == 200
    response = result.json()

    print(response)

    doc = get_campaign(mock_mongo_client, campaign_id)
    assert len(doc['comments']) == 2
    new_comment = doc['comments'][1]
    assert new_comment['user']['userId'] == payload['userId']
    assert new_comment['text'] == payload['text']
    assert new_comment['replies'] == []
    assert new_comment['_id'] == response['commentId']


def test_post_reply(mock_mongo_client, monkeypatch):
    monkeypatch.setenv("DB_NAME", "charitydb")
    monkeypatch.setenv("MONGO_URI", str(mock_mongo_client.address))
    monkeypatch.setenv("USER_SERVICE_URL", "http://mock-user-service")

    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client

    def mock_get(*args, **kwargs):
        return MockUserResponse()

    monkeypatch.setattr(requests, 'get', mock_get)

    payload = {
        'userId': 12,
        'text': "This is a test reply.",
        'campaignId': campaign_id
    }

    commentId = "6622f0b7a12c4d91f9b00002"

    result = test_client.put(f"/reply/{commentId}", json=payload)

    assert result.status_code == 200
    response = result.json()

    print(response)

    doc = get_campaign(mock_mongo_client, campaign_id)
    comment = next((c for c in doc['comments'] if c['_id'] == commentId), None)
    assert comment is not None
    assert len(comment['replies']) == 1
    new_reply = comment['replies'][0]
    assert new_reply['user']['userId'] == payload['userId']
    assert new_reply['text'] == payload['text']
    assert new_reply['_id'] == response['replyId']
