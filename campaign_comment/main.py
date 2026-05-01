from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, UploadFile, status
from typing import Annotated, List

from fastapi.responses import FileResponse

from .models.ReportInput import ReportInput
from .repository.reportRepository import create_image, create_report, get_image

from .models.CommentInput import CommentInput
from .models.CreateCampaignInput import CreateCampaignInput
from .models.UpdateCampaignInput import UpdateCampaignInput
from .repository.campaignRepository import find_campaign_by_owner, find_campaign_by_title, increment_campaign_current, decrement_campaign_current, like_campaign
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
    campaings = get_all_campaigns(mongo_client, page)
    return {'campaigns' : campaings}

@app.get("/campaign/{id}")
def get_campaign_by_id(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], id : str):
    campaign = get_campaign(mongo_client, id)
    
    if campaign is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    return {'campaign' : campaign}

@app.post("/campaign")
def create_new_campaign(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], input : CreateCampaignInput):
    campaignId = create_campaign(mongo_client, input.title, input.description, input.videolink, input.ownerId, datetime.now(), input.goal)
    return {"campaignId" : campaignId}

@app.get("/search")
def search_campaigns_by_title(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], title : str):
    return {"campaigns" : find_campaign_by_title(mongo_client, title)}

@app.get("/search/owner")
def search_campaigns_by_owner(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], ownerId : int):
    return {"campaigns" : find_campaign_by_owner(mongo_client, ownerId)}

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
    
    

@app.put('/reply/{id}')
def post_reply(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], id : str, input: CommentInput):
    try:
        replyId = create_reply(mongo_client, id, input.userId, input.text, input.campaignId)
        
        return {"replyId" : replyId}
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if str(e) == "Failed to add reply":
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add reply")
    
@app.post('/report')
def post_report(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], input: ReportInput):
    try:
        reportId = create_report(mongo_client, input.campaignId, input.reportTitle, input.amount)
        
        return {"reportId" : reportId}
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if str(e) == "Failed to add report":
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add report")
        
@app.post('/image/{reportId}/{campaignId}')
def post_image(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], reportId : str, campaignId : str, images : List[UploadFile]):
    try:
        image_names = create_image(mongo_client, reportId, campaignId, images)
        
        return {"imageNames" : image_names}
    
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if str(e) == "Failed to add image":
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add image")
        if str(e) == "Invalid image format. Only JPEG and PNG are allowed.":
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid image format. Only JPEG and PNG are allowed.")
        
        
@app.get('/image/{name}')
def get_image_endpoint(name:str):
    try:
        image_path = get_image(name)
        return FileResponse(image_path)
    
    except Exception as e:
        if str(e) == "Image not found":     
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Image not found")
        if str(e) == "Failed to get image":
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get image")
        
@app.put('/like/{campaignId}/{userId}')
def like_campaign_endpoint(mongo_client: Annotated[MongoClient, Depends(get_mongo_client)], campaignId : str, userId : int):
    try:
        result = like_campaign(mongo_client, campaignId, userId)
        
        if not result:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    except Exception as e:
        if str(e) == "Campaign not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if str(e) == "User has already liked this campaign":
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="User has already liked this campaign")
        if str(e) == "User not found":
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found")
