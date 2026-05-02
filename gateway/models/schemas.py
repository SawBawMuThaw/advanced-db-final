from pydantic import BaseModel
from typing import Optional


# -----------------------------
# AUTH
# -----------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


# -----------------------------
# CAMPAIGN
# -----------------------------
class CampaignCreate(BaseModel):
    title: str
    description: str
    goal: float
    videolink: str
    ownerId: Optional[int] = None


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    videolink: Optional[str] = None
    close: Optional[bool] = None


# -----------------------------
# DONATION
# -----------------------------
class DonationCreate(BaseModel):
    userID: Optional[int] = None
    campaignID: str
    amount: float
    time: str


# -----------------------------
# COMMENT
# -----------------------------
class CommentCreate(BaseModel):
    campaignId: str
    userId: Optional[int] = None
    text: str


# -----------------------------
# REPORT
# -----------------------------
class ReportCreate(BaseModel):
    campaignId: str
    reportTitle: str
    amount: float
