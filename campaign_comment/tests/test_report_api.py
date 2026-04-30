import pytest
from mongomock.mongo_client import MongoClient as MockMongoClient
from bson import ObjectId
from datetime import datetime
from fastapi import UploadFile
from fastapi.testclient import TestClient
from ..main import app, get_mongo_client
import io,os

test_client = TestClient(app)

@pytest.fixture
def campaign_id() -> str:
    return str("6622f0b7a12c4d91f9b00123")

@pytest.fixture
def mock_mongo_client():
    return MockMongoClient()

@pytest.fixture
def mock_db(mock_mongo_client, campaign_id):
    db = mock_mongo_client['charitydb']
    db.create_collection('campaigns')
    doc = {
        '_id': ObjectId(campaign_id),
        'goal': 50000.0,
        'current': 7350.0,
        'available': 7350.0,
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

def test_create_report(mock_mongo_client, mock_db, campaign_id, monkeypatch):
    
    monkeypatch.setenv("DB_NAME", "charitydb")
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    payload = {
        'campaignId' : campaign_id,
        'reportTitle' : "Bought boats",
        'amount' : 5000.0
    }
    
    response = test_client.post('/report', json=payload)
    
    assert response.status_code == 200
    reportId = response.json().get("reportId")
    
    assert reportId is not None
    
    doc = mock_db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    reports = doc.get("reports", [])
    assert any(report["reportTitle"] == payload['reportTitle'] and report["amount"] == payload['amount']
               and report['_id'] == reportId for report in reports)
    
def test_create_image(mock_mongo_client, mock_db, campaign_id, monkeypatch, tmpdir):
    monkeypatch.setenv("DB_NAME", "charitydb")
    image_folder = tmpdir.mkdir("images")
    monkeypatch.setenv("IMAGE_FOLDER_PATH", str(image_folder))
    
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    reportTitle = "Bought boats for water transport"
    amount = 1000.0
    
    payload = {
        'campaignId' : campaign_id,
        'reportTitle' : reportTitle,
        'amount' : amount
    }
    
    response = test_client.post('/report', json=payload)
    reportId = response.json().get("reportId")
    
    image_path = os.path.join(os.path.dirname(__file__), 'test_image.png')
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    files = {'images': ('test_image.png', io.BytesIO(image_bytes), 'image/png')}
    response = test_client.post(f'/image/{reportId}/{campaign_id}', files=files)
    
    assert response.status_code == 200
    image_names = response.json().get("imageNames")
    
    for name in image_names:
        image_path = image_folder.join(name)
        assert image_path.check()
        with open(image_path, 'rb') as f:
            assert f.read() == image_bytes
            
def test_get_image(mock_mongo_client, mock_db, campaign_id, monkeypatch, tmpdir):
    monkeypatch.setenv("DB_NAME", "charitydb")
    image_folder = tmpdir.mkdir("images")
    monkeypatch.setenv("IMAGE_FOLDER_PATH", str(image_folder))
    
    app.dependency_overrides[get_mongo_client] = lambda: mock_mongo_client
    
    reportTitle = "Bought boats for water transport"
    amount = 1000.0
    
    payload = {
        'campaignId' : campaign_id,
        'reportTitle' : reportTitle,
        'amount' : amount
    }
    
    response = test_client.post('/report', json=payload)
    reportId = response.json().get("reportId")
    
    image_path = os.path.join(os.path.dirname(__file__), 'test_image.png')
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    files = {'images': ('test_image.png', io.BytesIO(image_bytes), 'image/png')}
    response = test_client.post(f'/image/{reportId}/{campaign_id}', files=files)
    
    assert response.status_code == 200
    image_names = response.json().get("imageNames")
    
    for name in image_names:
        response = test_client.get(f'/image/{name}')
        assert response.status_code == 200
        assert response.content == image_bytes