from datetime import datetime
from bson import ObjectId
import dotenv
import os
from ..models.campaign import Campaign, Info
from ..models.user import User
import requests

dotenv.load_dotenv()

def create_campaign(mongo_client, title : str, description : str, videolink : str, ownerId : int, created : datetime, goal : float):
    db_name = os.getenv("DB_NAME")
    user_url = os.getenv("USER_SERVICE_URL")
    
    db = mongo_client[db_name]
    
    
    if 'campaigns' not in db.list_collection_names():
        db.create_collection('campaigns')
    
    collection = db['campaigns']
    
    response = requests.get(user_url + f"/user/{ownerId}")
    
    if(response.status_code != 200):
        raise Exception(f"Failed to retrieve user with ID {ownerId}. Status code: {response.status_code}")
    
    username = response.json().get("username")
    
    info = Info(title=title, description=description, videolink=videolink, owner=User(userId=ownerId, username=username), likes=0, likedBy=[], created=created)
    new_campaign = Campaign(goal=goal, current=0, isOpen=True, info=info, comments=[])
    
    # payload = new_campaign.model_dump(by_alias=True, exclude_none=True)
    payload = new_campaign.model_dump(by_alias=True, exclude=['campaignID'])
    result = collection.insert_one(payload)

    return str(result.inserted_id)

def get_campaign(mongo_client, campaign_id : str):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    result = collection.find_one({"_id" : ObjectId(campaign_id)})
    
    return result