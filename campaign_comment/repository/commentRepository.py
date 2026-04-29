import os

from bson import ObjectId
from bson.errors import InvalidId
from ..models.comment import Comment
from ..models.user import User
import requests


def _get_username(userId: int) -> str:
    user_url = os.getenv("USER_SERVICE_URL", "")
    response = requests.get(user_url + f"/user/{userId}")
    return response.json().get('username')


def _normalize_comment_id(commentId: str):
    try:
        return ObjectId(commentId)
    except (InvalidId, TypeError):
        return commentId

def create_comment(mongo_client, userId: int, text : str, campaignId: str):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    campaigns = db['campaigns']
    
    doc = campaigns.find_one({"_id" : ObjectId(campaignId)})
    
    if doc is None:
        raise Exception("Campaign not found")
    
    username = _get_username(userId)
    commentId = str(ObjectId())
    comment = Comment(_id=commentId, user=User(userId=userId, username=username), text=text, replies=[]).model_dump(by_alias=True, exclude_none=True)
    
    filter = {'_id' : ObjectId(campaignId)}
    update_operation = {'$push' : {'comments' : comment}}
    result = campaigns.update_one(filter, update_operation)
    
    if result.modified_count == 0:
        raise Exception("Failed to add comment")
    
    return commentId

def create_reply(mongo_client, commentId : str, userId: int, text : str, campaignId: str):
    db_name = os.getenv("DB_NAME")
    
    db = mongo_client[db_name]
    campaigns = db['campaigns']
    
    doc = campaigns.find_one({"_id" : ObjectId(campaignId)})
    
    if doc is None:
        raise Exception("Campaign not found")
    
    username = _get_username(userId)
    replyId = str(ObjectId())
    comment = Comment(_id=replyId, user=User(userId=userId, username=username), text=text, replies=[]).model_dump(by_alias=True, exclude_none=True)
    
    filter = {'_id' : ObjectId(campaignId)}
    update_operation = {'$push' : {'comments.$[c].replies' : comment}}
    array_filters = [{'c._id' : _normalize_comment_id(commentId)}]
    result = campaigns.update_one(filter, update_operation, array_filters=array_filters)
    
    if result.modified_count == 0:
        raise Exception("Failed to add reply")
    
    return replyId
