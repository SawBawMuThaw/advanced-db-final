import os
from mongomock import MongoClient as MockMongoClient
import pytest
from ..repository.campaignRepository import create_campaign, get_campaign, get_all_campaigns, update_campaign
from ..repository.campaignRepository import increment_campaign_current, decrement_campaign_current
from datetime import datetime
from bson import ObjectId
import requests
import uuid 
import random
from ..main import app, get_mongo_client
from fastapi.testclient import TestClient
from ..models.campaign import Campaign, Info

test_client = TestClient(app)

uuids = []
for i in range(1,11):
    uuids.append(str(ObjectId()))

@pytest.fixture
def mock_mongo_client():
    return MockMongoClient()

# app.dependency_overrides[get_mongo_client] = lambda : MockMongoClient()

@pytest.fixture
def mock_db(mock_mongo_client):
    db = mock_mongo_client['charitydb']
    db.create_collection('campaigns')
    docs = []
    for i in range(1,11):
        id = uuids[i-1]
        goal = random.randrange(1000, 10000)
        current = random.randrange(0, goal)
        isOpen = random.choice([True, False])
        title = f"Campaign {i}"
        description = f"This is the description for Campaign {i}."
        videolink = f"https://example.com/campaign-video-{i}"
        likes = random.randint(0, 50)
        likedBy = random.sample(range(1, 100), k=likes)
        ownerId = random.randint(1, 100)
        username = f"user{ownerId}"
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(2023, 2025)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        created = datetime(year, month, day, hour, minute, 0)
        comments = []
        
        doc = {
            '_id': ObjectId(id),
            'goal': goal,
            'current': current,
            'isOpen': isOpen,
            'info': {
                'title': title,
                'owner': {
                    'userId': ownerId,
                    'username': username
                },
                'description': description,
                'videolink': videolink,
                'likes': likes,
                'likedBy': likedBy,
                'created': created
            },
            'comments': comments
        }
        docs.append(doc)
    db.campaigns.insert_many(docs)
    return db

def test_campaign_get(mock_db, mock_mongo_client, monkeypatch):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    campaign_id = str(uuids[1])
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    
    doc['_id'] = str(doc['_id'])
    doc = Campaign.model_validate(doc).model_dump(by_alias=False, exclude_none=True,mode='json')
    
    # print(campaign_id)
    result = test_client.get(f"/campaign/{campaign_id}")
    
    # print(result.json())
    # print(doc)
    
    assert result.status_code == 200
    assert result.json() == doc
    
    
def test_campaign_get_all(mock_db, monkeypatch, mock_mongo_client):
    
    page = 1
    result = test_client.get(f"/campaign?page={page}")
    
    assert result.status_code == 200
    assert len(result.json()) == 6
    
    page = 2
    result = test_client.get(f"/campaign?page={page}")
    
    assert result.status_code == 200
    assert len(result.json()) == 4
    

class MockUserResponse:
    def __init__(self):
        self.status_code = 200

    @staticmethod
    def json():
        return {'username': 'testuser'}
               
def test_campaign_create_campaign(mock_db, monkeypatch, mock_mongo_client):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    def mock_get(*args, **kwargs):
        return MockUserResponse()

    monkeypatch.setattr(requests, 'get', mock_get)
    
    title = "New Campaign"
    description = "This is a new campaign."
    videolink = "https://example.com/new-campaign-video"
    ownerId = 123
    goal = 5000
    
    payload = {
        "title": title,
        "description": description,
        "videolink": videolink,
        "ownerId": ownerId,
        "goal": goal
    }
    
    result = test_client.post("/campaign", json=payload)
    
    assert result.status_code == 200
    response_json = result.json()
    
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(response_json)})
    assert doc is not None
    assert doc['info']['title'] == title
    assert response_json == str(doc['_id'])
    
def test_update_campaign(mock_db, monkeypatch, mock_mongo_client):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    campaign_id = str(uuids[0])
    new_title = "Updated Campaign Title"
    new_description = "This is the updated description."
    new_videolink = "https://example.com/updated-campaign-video"
    
    payload = {
        "title": new_title,
        "description": new_description,
        "videolink": new_videolink,
    }
    
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    isOpen = doc['isOpen']
    
    result = test_client.put(f"/campaign/{campaign_id}", json=payload)
    
    assert result.status_code == 200
    
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    assert doc is not None
    assert doc['info']['title'] == new_title
    assert doc['info']['description'] == new_description
    assert doc['info']['videolink'] == new_videolink
    assert doc['isOpen'] == isOpen
    
    bogus_campaign_id = str(ObjectId())
    result = test_client.put(f"/campaign/{bogus_campaign_id}", json=payload)
    
    assert result.status_code == 404
    assert result.json() == {"detail": "Campaign not found"}
    
    
def test_increment_campaign_current(mock_db, monkeypatch, mock_mongo_client):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    campaign_id = str(uuids[2])
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    prev_current = doc['current']
    amount = 100
    
    result = test_client.put(f"/increment/{campaign_id}/{amount}")
    
    assert result.status_code == 200
    
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    assert doc['current'] == prev_current + amount
    
    goal = doc['goal']
    amount = goal - doc['current'] + 1
    
    result = test_client.put(f"/increment/{campaign_id}/{amount}")
    
    assert result.status_code == 400
    assert result.json() == {"detail": "Amount exceeds campaign goal"}
    
    bogus_campaign_id = str(ObjectId())
    result = test_client.put(f"/increment/{bogus_campaign_id}/{amount}")
    
    assert result.status_code == 404
    assert result.json() == {"detail": "Campaign not found"}
    
def test_decrement_campaign_current(mock_db, monkeypatch, mock_mongo_client):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    campaign_id = str(uuids[3])
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    prev_current = doc['current']
    amount = 100
    
    result = test_client.put(f"/decrement/{campaign_id}/{amount}")
    
    assert result.status_code == 200
    
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    assert doc['current'] == prev_current - amount
    
    amount = doc['current'] + 1
    
    result = test_client.put(f"/decrement/{campaign_id}/{amount}")
    
    assert result.status_code == 400
    assert result.json() == {"detail": "Amount exceeds campaign current"}
    
    bogus_campaign_id = str(ObjectId())
    result = test_client.put(f"/decrement/{bogus_campaign_id}/{amount}")
    
    assert result.status_code == 404
    assert result.json() == {"detail": "Campaign not found"}
    
def test_find_campaign_by_title(mock_db, monkeypatch, mock_mongo_client):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    campaign_id = str(uuids[4])
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    
    title = doc['info']['title']
    
    response = test_client.get(f"/search?title={title}")
    result = response.json()
    
    assert response.status_code == 200
    assert len(result) == 1
    assert result[0]['info']['title'] == title
    
def test_find_campaign_by_owner(mock_db, monkeypatch, mock_mongo_client):
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    campaign_id = str(uuids[5])
    doc = mock_db.campaigns.find_one({'_id' : ObjectId(campaign_id)})
    
    ownerId = doc['info']['owner']['userId']
    
    response = test_client.get(f"/search/owner?ownerId={ownerId}")
    result = response.json()
    
    assert response.status_code == 200
    assert len(result) >= 1
    assert result[0]['info']['owner']['userId'] == ownerId