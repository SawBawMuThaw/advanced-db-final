import os
from mongomock import MongoClient as MockMongoClient
import pytest
from ..repository.campaignRepository import create_campaign, get_campaign
from datetime import datetime
from bson import ObjectId
import requests


@pytest.fixture
def mock_mongo_client():
    return MockMongoClient()


@pytest.fixture
def mock_db(mock_mongo_client):
    db = mock_mongo_client['charitydb']
    db.create_collection('campaigns')
    doc = {
        '_id': ObjectId("6622f0b7a12c4d91f9b00123"),
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
        'comments': [
            {
                '_id': "cmt-1001",
                'user': {
                    'userId': 12,
                    'username': "donor_ana"
                },
                'text': "Happy to support this cause!",
                'replies': [
                    {
                        '_id': "cmt-1001-r1",
                        'user': {
                            'userId': 5,
                            'username': "testuser"
                        },
                        'text': "Thank you so much for your support!",
                        'replies': []
                    }
                ]
            }
        ]
    }
    db.campaigns.insert_one(doc)
    return db


class MockUserResponse:

    def __init__(self):
        self.status_code = 200

    @staticmethod
    def json():
        return {'username': 'testuser'}


def test_create_campaign(mock_mongo_client, mock_db, monkeypatch):
    # setting up mock values
    monkeypatch.setenv('DB_NAME', 'charitydb')
    monkeypatch.setenv('USER_SERVICE_URL', 'http://localhost:3000')

    def mock_get(*args, **kwargs):
        return MockUserResponse()

    monkeypatch.setattr(requests, 'get', mock_get)

    # Actual test
    title = 'Test Campaign'
    description = "This is a test campaign."
    videolink = "http://example.com/video"
    ownerId = 5
    created = datetime.now()
    goal = 50000

    inserted_id = create_campaign(
        mock_mongo_client, title, description, videolink, ownerId, created, goal)

    assert isinstance(inserted_id, str)
    assert len(inserted_id) > 0

    collection = mock_db['campaigns']
    inserted_doc = collection.find_one({"_id": ObjectId(inserted_id)})

    assert inserted_doc is not None
    assert inserted_doc['info']['title'] == title
    assert inserted_doc['info']['description'] == description
    assert inserted_doc['info']['videolink'] == videolink
    assert inserted_doc['info']['owner']['userId'] == ownerId
    assert inserted_doc['goal'] == goal
    assert inserted_doc['current'] == 0
    assert inserted_doc['isOpen'] == True


def test_get_campaign(mock_mongo_client, mock_db, monkeypatch):
    monkeypatch.setenv('DB_NAME', 'charitydb')

    campaign_id = "6622f0b7a12c4d91f9b00123"
    
    campaign_doc = get_campaign(mock_mongo_client, campaign_id=campaign_id)
    
    assert campaign_doc is not None
    assert campaign_doc['_id'] == ObjectId(campaign_id)
    assert campaign_doc['info']['title'] == "Clean Water for Barangay Malinis"
    
    campaign_id = "6622f0b7a12c4d91f9b99999"
    
    campaign_doc = get_campaign(mock_mongo_client, campaign_id=campaign_id)
    
    assert campaign_doc is None


def test_get_all_campaigns(mocker, monkeypatch):
    pass


def test_update_campaign(mocker, monkeypatch):
    pass


def test_increment_campaign_current(mocker, monkeypatch):
    pass


def test_decrement_campaign_current(mocker, monkeypatch):
    pass
