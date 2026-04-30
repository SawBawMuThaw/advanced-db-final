import io
import os
from io import BytesIO

from bson import ObjectId
import pytest
from fastapi import UploadFile
from mongomock.mongo_client import MongoClient as MockMongoClient
from ..repository.reportRepository import create_report, create_image, get_image
from datetime import datetime

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

def test_create_report(mock_db, campaign_id, mock_mongo_client, monkeypatch):
    monkeypatch.setenv("DB_NAME", "charitydb")
    reportTitle = "Bought boats for water transport"
    amount = 1000.0
    
    doc = mock_db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    prev = doc['available']
    
    reportId = create_report(mock_mongo_client, campaign_id, reportTitle, amount)
    
    # Verify the report was added to the campaign
    campaign_doc = mock_db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    assert campaign_doc is not None
    reports = campaign_doc.get("reports", [])
    assert any(report["reportTitle"] == reportTitle and report["amount"] == amount
               and report['_id'] == reportId for report in reports)
    
    assert campaign_doc["available"] == prev - amount
    
def test_create_image(tmpdir, mock_db, mock_mongo_client, monkeypatch, campaign_id):
    image_dir = tmpdir.mkdir('images')
    monkeypatch.setenv("IMAGE_FOLDER_PATH", str(image_dir))
    monkeypatch.setenv("DB_NAME", "charitydb")
    
    reportTitle = "Bought boats for water transport"
    amount = 1000.0
    
    reportId = create_report(mock_mongo_client, campaign_id, reportTitle, amount)
    
    image_path_source = os.path.join(os.path.dirname(__file__), 'test_image.png')
    with open(image_path_source, 'rb') as f:
        image_bytes = f.read()

    upload = type('DummyUploadFile', (), {})()
    upload.content_type = 'image/png'
    upload.filename = 'test_image.png'
    upload.file = io.BytesIO(image_bytes)

    image_names = create_image(mock_mongo_client, reportId, campaign_id, [upload])

    for name in image_names:
        image_path = image_dir.join(name)
        assert os.path.exists(image_path)
        with open(image_path, 'rb') as f:
            assert f.read() == image_bytes
            
    doc = mock_db.campaigns.find_one({"_id": ObjectId(campaign_id)})
    reports = doc.get("reports", [])
    assert any(report['_id'] == reportId and "attachedImages" in report and all(name in report["attachedImages"] for name in image_names)
               for report in reports)
    # print(reports[0]['attachedImages'])
    
def test_get_image(mock_db, monkeypatch, tmpdir, mock_mongo_client, campaign_id):
    image_dir = tmpdir.mkdir('images')
    monkeypatch.setenv("IMAGE_FOLDER_PATH", str(image_dir))
    monkeypatch.setenv("DB_NAME", "charitydb")
    
    reportTitle = "Bought boats for water transport"
    amount = 1000.0
    
    reportId = create_report(mock_mongo_client, campaign_id, reportTitle, amount)
    
    image_path_source = os.path.join(os.path.dirname(__file__), 'test_image.png')
    with open(image_path_source, 'rb') as f:
        image_bytes = f.read()

    upload = type('DummyUploadFile', (), {})()
    upload.content_type = 'image/png'
    upload.filename = 'test_image.png'
    upload.file = io.BytesIO(image_bytes)

    image_names = create_image(mock_mongo_client, reportId, campaign_id, [upload])
    
    for name in image_names:
        image_path = get_image(name)
        with open(image_path, 'rb') as f:
            assert f.read() == image_bytes