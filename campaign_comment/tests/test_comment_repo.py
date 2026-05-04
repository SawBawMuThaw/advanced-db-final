import pytest
from mongomock import MongoClient as MockMongoClient
from bson import ObjectId
import requests
from datetime import datetime
from testcontainers.mongodb import MongoDbContainer
from pymongo import MongoClient

from ..repository.commentRepository import create_comment, create_reply, get_most_active_commenters
from ..repository.campaignRepository import get_campaign

campaign_id = "6622f0b7a12c4d91f9b00123"
doc = {
    '_id': ObjectId(campaign_id),
    'goal': 50000.0,
    'current': 7350.0,
    'isOpen': True,
    'info': {
        'title': "Clean Water for Barangay Malinis",
        'owner': {
            'userId': 5,
            'username': "testuser"
        },
        'description': "Funding deep-well pumps and water filters for 120 families.",
        'videolink': "https://example.com/campaign-video",
        'likes': 18,
        'likedBy': [2, 4, 9, 11, 15],
        'created': datetime(2026, 4, 19, 10, 30, 0)
    },
}
comment = {
    '_id': ObjectId("5234f0b7a12c4d91f9b00001"),
    'user': {
        'userId': 12,
        'username': "donor_ana"
    },
    'text': "Happy to support this cause!",
    'campaignId': ObjectId(campaign_id),
    'parentId': None
}
comment2 = {
    '_id': ObjectId("5234f0b7a12c4d91f9b00002"),
    'user': {
        'userId': 5,
        'username': "testuser"
    },
    'text': "Thank you so much for your support!",
    'campaignId': ObjectId(campaign_id),
    'parentId': ObjectId("5234f0b7a12c4d91f9b00001")
}


@pytest.fixture
def mock_mongo_client():
    return MockMongoClient()


@pytest.fixture
def mock_db(mock_mongo_client):
    db = mock_mongo_client['charitydb']
    db.create_collection('campaigns')
    db.campaigns.insert_one(doc)
    db.create_collection('comments')
    db.comments.insert_one(comment)
    db.comments.insert_one(comment2)
    return db


class MockUserResponse:

    def __init__(self):
        self.status_code = 200

    @staticmethod
    def json():
        return {'username': 'testuser'}


def test_add_comment(mock_db, mock_mongo_client, monkeypatch):

    def mock_get(*args, **kwargs):
        return MockUserResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setenv("DB_NAME", "charitydb")
    monkeypatch.setenv("USER_SERVICE_URL", "http://mock-user-service")

    userId = 12
    text = "Happy to support this cause!"
    campaignId = campaign_id
    commentId = "cmt-1001"

    commentId = create_comment(mock_mongo_client, userId, text, campaignId)

    assert commentId is not None
    assert isinstance(commentId, str)
    assert len(commentId) > 0

    campaign = get_campaign(mock_mongo_client, campaignId)
    assert campaign is not None
    comments = campaign.get('comments', [])
    assert len(comments) == 2

    bogusCampaignId = "6622f0b7a12c4d91f9b00000"
    with pytest.raises(Exception) as excinfo:
        create_comment(mock_mongo_client, userId, text, bogusCampaignId)
        assert "Campaign not found" in str(excinfo.value)


def test_reply(mock_db, mock_mongo_client, monkeypatch):

    def mock_get(*args, **kwargs):
        return MockUserResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setenv("DB_NAME", "charitydb")
    monkeypatch.setenv("USER_SERVICE_URL", "http://mock-user-service")

    userId = 5
    text = "Thank you so much for your support!"
    campaignId = campaign_id
    commentId = "5234f0b7a12c4d91f9b00001"
    replyId = create_reply(mock_mongo_client, commentId,
                           userId, text, campaignId)

    assert replyId is not None
    assert isinstance(replyId, str)
    assert len(replyId) > 0

    campaign = get_campaign(mock_mongo_client, campaignId)
    assert campaign is not None
    comments = campaign.get('comments', [])
    assert len(comments) == 1
    root_comment = next(
        (c for c in comments if c['_id'] == commentId), None)
    assert root_comment is not None
    assert len(root_comment['replies']) == 2
    assert root_comment['replies'][1]['text'] == text
    assert root_comment['replies'][1]['_id'] == replyId

def test_get_most_active_commenters(mock_db, mock_mongo_client, monkeypatch):
    monkeypatch.setenv("DB_NAME", "charitydb")
    monkeypatch.setenv("USER_SERVICE_URL", "http://mock-user-service")

    active_commenters = get_most_active_commenters(mock_mongo_client, top_n=5)

    assert isinstance(active_commenters, list)
    assert len(active_commenters) == 2
    assert active_commenters[0]['userId'] == 5
    assert active_commenters[0]['username'] == 'testuser'
    assert active_commenters[0]['totalComments'] == 1
    assert active_commenters[0]['campaignCount'] == 1