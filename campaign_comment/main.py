from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated

from .models.CommentInput import CommentInput
from .models.CreateCampaignInput import CreateCampaignInput
from .models.UpdateCampaignInput import UpdateCampaignInput
from .repository.campaignRepository import find_campaign_by_owner, find_campaign_by_title, increment_campaign_current, decrement_campaign_current
from .repository.campaignRepository import create_campaign, get_campaign, get_all_campaigns, update_campaign
from .repository.commentRepository import create_comment, create_reply
from pymongo import MongoClient
import dotenv
import os
import json

dotenv.load_dotenv()

app = FastAPI()

def get_mongo_client():
    uri = os.getenv("MONGO_URI")
    with MongoClient(uri) as client:
        yield client
        
@app.get("/campaign")
def get_all_campaigns_endpoint(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], page : int | None = 1):
    return get_all_campaigns(mongo_client, page)

@app.get("/campaign/{id}")
def get_campaign_by_id(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], id : str):
    return get_campaign(mongo_client, id)

@app.post("/campaign")
def create_new_campaign(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], input : CreateCampaignInput):
    return create_campaign(mongo_client, input.title, input.description, input.videolink, input.ownerId, datetime.now(), input.goal)

@app.get("/search")
def search_campaigns_by_title(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], title : str):
    return find_campaign_by_title(mongo_client, title)

@app.get("/search/owner")
def search_campaigns_by_owner(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], ownerId : int):
    return find_campaign_by_owner(mongo_client, ownerId)

@app.put("/campaign/{id}")
def update_campaign_by_id(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], input : UpdateCampaignInput, id : str):
    result = update_campaign(mongo_client, id, input.title, input.description, input.videolink, input.close)
    
    if not result:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")

@app.put("/increment/{id}/{amount}")
def increment_campaign(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], id : str, amount : float):
    try:
        result = increment_campaign_current(mongo_client, id, amount)
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        elif str(e) == "Amount exceeds campaign goal":
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Amount exceeds campaign goal")
        
    if not result:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Amount exceeds campaign goal")

@app.put("/decrement/{id}/{amount}")
def decrement_campaign(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], id : str, amount : float):
    try:
        result = decrement_campaign_current(mongo_client, id, amount)
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        elif str(e) == "Amount exceeds campaign current":
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Amount exceeds campaign current")
    
    if not result:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Amount exceeds campaign current")
    
@app.post('/comment')
def post_comment(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], input: CommentInput):
    try:
        commentId = create_comment(mongo_client, input.userId, input.text, input.campaignId)
        
        return {"commentId" : commentId}
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if str(e) == "Failed to add comment":
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add comment")
    
    

@app.post('/reply/{id}')
def post_reply(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], id : str, input: CommentInput):
    try:
        replyId = create_reply(mongo_client, id, input.userId, input.text, input.campaignId)
        
        return {"replyId" : replyId}
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if str(e) == "Failed to add reply":
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add reply")
    
    