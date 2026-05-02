from datetime import datetime
import dotenv
from fastapi import UploadFile
from typing import List
from pymongo import MongoClient
import os
from bson import ObjectId
from ..models.report import Report
import hashlib

dotenv.load_dotenv('../.env')

def create_report(mongo_client: MongoClient, campaign_id : str, reportTitle : str, amount : float):
    db_name = os.getenv("DB_NAME")
    db = mongo_client[db_name]
    campaigns = db["campaigns"]
    
    doc = campaigns.find_one({"_id" : ObjectId(campaign_id)})
    
    if doc is None:
        raise ValueError("Campaign not found")  
    
    reportId = str(ObjectId())
    report = Report(_id = reportId, reportTitle=reportTitle, time=datetime.now(), amount=amount).model_dump(by_alias=True, exclude_none=True)
    
    filter = {"_id" : ObjectId(campaign_id)}
    update_operation = {"$push" : {"reports" : report}}
    
    # TODO - check if we should keep track of amount spent in campaign document and update it here as well
    result = campaigns.update_one(filter, update_operation)
    
    if result.modified_count > 0:
        update_operation = {"$inc" : {"available" : -amount}}
        campaigns.update_one(filter, update_operation)
        return reportId
    else:
        raise ValueError("Failed to add report")

def get_report(mongo_client: MongoClient, report_id : str):
    db_name = os.getenv("DB_NAME")
    db = mongo_client[db_name]
    campaigns = db["campaigns"]

    campaign = campaigns.find_one(
        {"reports._id": report_id},
        {"reports.$": 1}
    )

    if campaign is None or not campaign.get("reports"):
        raise ValueError("Report not found")

    return campaign["reports"][0]

def create_image(mongo_client: MongoClient, reportId : str, campaignId : str, images : List[UploadFile]):
    db_name = os.getenv("DB_NAME")
    image_folder_path = os.getenv("IMAGE_FOLDER_PATH")
    db = mongo_client[db_name]
    campaigns = db["campaigns"]
    
    if any(image.content_type not in ["image/jpeg", "image/png"] for image in images):
        raise ValueError("Invalid image format. Only JPEG and PNG are allowed.")
    
    image_names = []
    
    for img in images:
        image = img.file.read()
        hash = hashlib.sha256(img.filename.encode("utf-8")).hexdigest()
        format = img.content_type.split("/")[1]
        image_name = f"{hash}.{format}"
        image_path = os.path.join(image_folder_path, image_name)
        with open(image_path, "wb") as f:
            f.write(image)
            image_names.append(image_name)
    
    campaign = campaigns.find_one({"_id" : ObjectId(campaignId)})
    if campaign is None:
        raise ValueError("Campaign not found")

    reports = campaign.get("reports", [])
    for report in reports:
        if report.get("_id") == reportId:
            report.setdefault("attachedImages", [])
            report["attachedImages"].extend(image_names)
            break
    else:
        raise ValueError("Failed to add image")

    result = campaigns.update_one({"_id" : ObjectId(campaignId)}, {"$set" : {"reports" : reports}})
    
    if result.modified_count > 0:
        return image_names
    else:
        raise ValueError("Failed to add image")

def get_image(image_name : str):
    image_folder_path = os.getenv("IMAGE_FOLDER_PATH")
    image_path = os.path.join(image_folder_path, image_name)
    
    if not os.path.exists(image_path):
        raise ValueError("Image not found")
    
    return image_path
