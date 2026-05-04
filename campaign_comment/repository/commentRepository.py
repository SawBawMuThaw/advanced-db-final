import os

from bson import ObjectId
from bson.errors import InvalidId
import dotenv
from ..models.comment import Comment
from ..models.user import User
import requests
from bson import json_util

dotenv.load_dotenv('../.env')


def _get_username(userId: int) -> str:
    user_url = os.getenv("USER_SERVICE_URL", "")
    response = requests.get(user_url + f"/user/{userId}")
    return response.json().get('username')


def _normalize_comment_id(commentId: str):
    try:
        return ObjectId(commentId)
    except (InvalidId, TypeError):
        return commentId

# def create_comment(mongo_client, userId: int, text : str, campaignId: str):
#     db_name = os.getenv("DB_NAME")

#     db = mongo_client[db_name]
#     campaigns = db['campaigns']

#     doc = campaigns.find_one({"_id" : ObjectId(campaignId)})

#     if doc is None:
#         raise Exception("Campaign not found")

#     username = _get_username(userId)
#     commentId = str(ObjectId())
#     comment = Comment(_id=commentId, user=User(userId=userId, username=username), text=text, replies=[]).model_dump(by_alias=True, exclude_none=True)

#     filter = {'_id' : ObjectId(campaignId)}
#     update_operation = {'$push' : {'comments' : comment}}
#     result = campaigns.update_one(filter, update_operation)

#     if result.modified_count == 0:
#         raise Exception("Failed to add comment")

#     return commentId


def create_comment(mongo_client, userId: int, text: str, campaignId: str):
    db_name = os.getenv("DB_NAME")

    db = mongo_client[db_name]
    comments = db['comments']
    campaigns = db['campaigns']

    doc = campaigns.find_one({"_id": ObjectId(campaignId)})

    if doc is None:
        raise Exception("Campaign not found")

    username = _get_username(userId)

    comment = {
        'campaignId': ObjectId(campaignId),
        'parentId': None,
        'user': {
            'userId': userId,
            'username': username
        },
        'text': text,
    }

    result = comments.insert_one(comment)

    if result.inserted_id is None:
        raise Exception("Failed to add comment")

    return str(result.inserted_id)

# def create_reply(mongo_client, commentId : str, userId: int, text : str, campaignId: str):
#     db_name = os.getenv("DB_NAME")

#     db = mongo_client[db_name]
#     campaigns = db['campaigns']

#     doc = campaigns.find_one({"_id" : ObjectId(campaignId)})

#     if doc is None:
#         raise Exception("Campaign not found")

#     username = _get_username(userId)


#     replyId = str(ObjectId())
#     comment = Comment(_id=replyId, user=User(userId=userId, username=username), text=text, replies=[]).model_dump(by_alias=True, exclude_none=True)

#     filter = {'_id' : ObjectId(campaignId)}
#     update_operation = {'$push' : {'comments.$[c].replies' : comment}}
#     # we store comment Id as a string, not a ObjectId
#     array_filters = [{'c._id' : commentId}]
#     result = campaigns.update_one(filter, update_operation, array_filters=array_filters)

#     if result.modified_count == 0:
#         raise Exception("Failed to add reply")

#     return replyId

def create_reply(mongo_client, commentId: str, userId: int, text: str, campaignId: str):
    db_name = os.getenv("DB_NAME")

    db = mongo_client[db_name]
    comments = db['comments']
    campaigns = db['campaigns']

    doc = campaigns.find_one({"_id": ObjectId(campaignId)})

    if doc is None:
        raise Exception("Campaign not found")

    username = _get_username(userId)
    reply = {
        'campaignId': ObjectId(campaignId),
        'parentId': ObjectId(commentId),
        'user': {
            'userId': userId,
            'username': username
        },
        'text': text,
    }

    result = comments.insert_one(reply)

    if result.inserted_id is None:
        raise Exception("Failed to add reply")

    return str(result.inserted_id)


def get_most_active_commenters(mongo_client, top_n: int = 10):
    db_name = os.getenv("DB_NAME")

    db = mongo_client[db_name]
    comments = db['comments']

    pipeline = [
        {'$group': {
            '_id': {
                'userId': '$user.userId',
                'username': '$user.username'
            },
            'commentCount': {'$sum': 1},
            'uniqueCampaigns': {'$addToSet': '$campaignId'}
        }
        },
        {'$sort' : {'commentCount' : -1}},
        {'$limit' : top_n},
        {
            '$project' : {
                '_id' : 0,
                'userId' : '$_id.userId',
                'username' : '$_id.username',
                'totalComments' : '$commentCount',
                'campaignCount' : {'$size' : '$uniqueCampaigns'}
            }
        }
    ]

    results = comments.aggregate(pipeline)

    active_commenters = []
    for result in results:
        userId = result['userId']
        username = result['username']
        totalComments = result['totalComments']
        campaignCount = result['campaignCount']
        active_commenters.append(
            {'userId': userId, 'username': username, 'totalComments': totalComments, 'campaignCount': campaignCount})

    return active_commenters
