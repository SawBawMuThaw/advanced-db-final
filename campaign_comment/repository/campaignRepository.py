from datetime import datetime
from unittest import result
from bson import ObjectId
import dotenv
import os
from ..models.campaign import Campaign, Info
from ..models.user import User
import requests
from bson import json_util

dotenv.load_dotenv('../.env')

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

def get_comments(mongo_client, campaign_id : str):
    db_name = os.getenv("DB_NAME")
    db = mongo_client[db_name]
    collection = db['comments']
    
    results = list(collection.find({"campaignId" : ObjectId(campaign_id)}))

    comments_by_id = {}
    roots = []

    for comment in results:
        comment['_id'] = str(comment['_id'])
        comment['campaignId'] = str(comment['campaignId'])
        if comment.get('parentId') is not None:
            comment['parentId'] = str(comment['parentId'])
        comment['replies'] = []
        comments_by_id[comment['_id']] = comment

    for comment in results:
        parent_id = comment.get('parentId')

        if parent_id and parent_id in comments_by_id:
            comments_by_id[parent_id]['replies'].append(comment)
        elif parent_id is None:
            roots.append(comment)

    return roots

def get_campaign(mongo_client, campaign_id : str):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    result = collection.find_one({"_id" : ObjectId(campaign_id)})
    
    if result is None:
        return None
    
    result['_id'] = str(result['_id'])
    result['comments'] = get_comments(mongo_client, campaign_id)
    campaign = Campaign.model_validate(result)
    campaign.comments = get_comments(mongo_client, campaign_id)
    return campaign.model_dump(by_alias=False, exclude_none=True)

def get_all_campaigns(mongo_client, page : int | None = 1):
    db_name = os.getenv("DB_NAME")
    page_size = 6
    
    offset = (page - 1) * page_size
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    results = collection.find().skip(offset).limit(page_size)
    
    campaigns = []
    for doc in results:
        doc['_id'] = str(doc['_id'])
        campaign = Campaign.model_validate(doc)
        campaign.comments = get_comments(mongo_client, campaign.campaignID)
        campaigns.append(campaign.model_dump(by_alias=False, exclude_none=True))
    return campaigns

def update_campaign(mongo_client, campaign_id : str, new_title : str = None, description : str = None,
                    videolink : str = None, close : bool = None):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    query_filter = {"_id" : ObjectId(campaign_id)}
    update_fields = {}
    
    if new_title is not None:
        update_fields['info.title'] = new_title
    if description is not None:
        update_fields['info.description'] = description 
    if videolink is not None:
        update_fields['info.videolink'] = videolink
    if close is not None:
        update_fields['isOpen'] = not close
    
    result = collection.update_one(query_filter, {'$set' : update_fields})
    
    return result.modified_count > 0

def increment_campaign_current(mongo_client, campaign_id : str, amount : float):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    query_filter = {"_id" : ObjectId(campaign_id)}
    update_operation = {"$inc" : {"current" : amount, "available" : amount}}
    
    doc = collection.find_one(query_filter)
    
    if doc is None:
        raise Exception("Campaign not found")
    
    if(doc['current'] + amount > doc['goal']):
        raise Exception("Amount exceeds campaign goal")
    else:
        result = collection.update_one(query_filter, update_operation)
    
    return result.modified_count > 0

def decrement_campaign_current(mongo_client, campaign_id : str, amount : float):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    query_filter = {"_id" : ObjectId(campaign_id)}
    update_operation = {"$inc" : {"current" : -amount, "available" : -amount}}
    
    doc = collection.find_one(query_filter)
    
    if doc is None:
        raise Exception("Campaign not found")
    
    if(doc['current'] - amount < 0):
        raise Exception("Amount exceeds campaign current")
    else:
        result = collection.update_one(query_filter, update_operation)
    
    return result.modified_count > 0

def find_campaign_by_title(mongo_client, title : str):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    results = collection.find({"info.title" : title})
    
    campaigns = []
    for doc in results:
        doc['_id'] = str(doc['_id'])
        campaign = Campaign.model_validate(doc)
        campaign.comments = get_comments(mongo_client, campaign.campaignID)
        campaigns.append(campaign.model_dump(by_alias=False, exclude_none=True))
    
    return campaigns

def find_campaign_by_owner(mongo_client, ownerId : int):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    results = collection.find({"info.owner.userId" : ownerId})
    
    campaigns = []
    for doc in results:
        doc['_id'] = str(doc['_id'])
        campaign = Campaign.model_validate(doc)
        campaign.comments = get_comments(mongo_client, campaign.campaignID)  
        campaigns.append(campaign.model_dump(by_alias=False, exclude_none=True))
    
    return campaigns

def like_campaign(mongo_client, campaign_id : str, userId : int):
    db_name = os.getenv("DB_NAME")
    user_service = os.getenv("USER_SERVICE_URL")
    
    db = mongo_client[db_name]
    collection = db['campaigns']
    
    query_filter = {"_id" : ObjectId(campaign_id)}
    
    doc = collection.find_one(query_filter)
    
    if doc is None:
        raise Exception("Campaign not found")
    
    response = requests.get(user_service + f"/user/{userId}")
    if response.status_code != 200:
        raise Exception("User not found")
    
    if userId in doc['info']['likedBy']:
        raise Exception("User has already liked this campaign")
    
    update_operation = {"$inc" : {"info.likes" : 1}, "$push" : {"info.likedBy" : userId}}
    
    result = collection.update_one(query_filter, update_operation)
    
    return result.modified_count > 0