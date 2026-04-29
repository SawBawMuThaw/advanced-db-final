from fastapi import FastAPI, HTTPException, status
from .models.DonationInput import DonationInput
from .models.CampaignInput import CampaignInput
from .models.CommentInput import CommentInput
from .models.UserInput import UserInput
import dotenv
import os
import requests

dotenv.load_dotenv()

app = FastAPI()

@app.post("/donate")
def record_donation(input: DonationInput):
    donation_url = os.getenv("USER_DONATION_SERVICE")
    campaign_url = os.getenv("CAMPAIGN_COMMENT_SERVICE")
    
    # check if campaign exists
    response = requests.get(campaign_url + f"/campaign/{input.campaignID}")
    
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    payload = {
        "userID" : input.userID,
        "campaignID" : input.campaignID,
        "amount" : input.amount,
        "time" : input.time
    }
    
    response = requests.post(donation_url + "/donate", json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record donation")
    
    donationId = response.json().get("donationId")
    
    response = requests.put(campaign_url + f"/increment/{input.campaignId}/{input.amount}")
    
    if response.status_code != 200:
        # Rollback the donation
        requests.delete(donation_url + f"/donate/{donationId}")
        
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record donation")
    
@app.post("/campaign")
def create_campaign(input : CampaignInput):
    campaign_url = os.getenv("CAMPAIGN_COMMENT_SERVICE")
    
    payload = {
        "title" : input.title,
        "description" : input.description,
        "goal" : input.goal,
        "videolink" : input.videolink,
        "ownerId" : input.ownerId
    }
    
    response = requests.post(campaign_url + "/campaign", json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create campaign")
    
    campaign_id = response.json().get('campaignId')
    return campaign_id

@app.post("/comment")
def create_comment(input : CommentInput):
    campaign_url = os.getenv("CAMPAIGN_COMMENT_SERVICE")
    
    # check if campaign exists
    response = requests.get(campaign_url + f"/campaign/{input.campaignId}")
    
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    payload = {
        "campaignId" : input.campaignId,
        "userId" : input.userId,
        "text" : input.text
    }
    
    response = requests.post(campaign_url + "/comment", json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create comment")
    
    comment_id = response.json().get('commentId')
    return comment_id

@app.post("/reply/{id}")
def create_reply(id : str, input : CommentInput):
    campaign_url = os.getenv("CAMPAIGN_COMMENT_SERVICE")
    
    # check if campaign exists
    response = requests.get(campaign_url + f"/campaign/{input.campaignId}")
    
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    payload = {
        "campaignId" : input.campaignId,
        "userId" : input.userId,
        "text" : input.text
    }
    
    response = requests.post(campaign_url + f"/reply/{id}", json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create reply")
    
    reply_id = response.json().get('replyId')
    return reply_id

@app.post("/register")
def create_user(input: UserInput):
    user_url = os.getenv("USER_DONATION_SERVICE")
    
    payload = {
        "username" : input.username,
        "email" : input.email,
        "password" : input.password
    }
    
    response = requests.post(user_url + "/register", json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
    
    user_id = response.json().get('userId')
    return user_id