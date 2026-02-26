from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional
import shutil
import os
import json
import logging
from app.gcs import upload_file_to_gcs

#Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic-fitness-mvp")

# Read required env var
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
if not GCS_BUCKET_NAME:
    logger.warning("GCS_BUCKET_NAME environment variable is not set.")
    
app = FastAPI(title="Agentic Fitness MVP")

class PlanResponse(BaseModel):
    plan_id: str
    message: Optional[str] = None
    front_gs_path: str
    side_gs_path: str
    back_gs_path: str
    metadata_gs_path: str

@app.get("/")
async def root():
    return {"ok": True, "service": "agentic-fitness-mvp", "version": "0.1.1"}

@app.post("/submit-assessment", response_model=PlanResponse)
async def submit_assessment(
goals: str = Form(...),
front_photo: UploadFile = File(...),
side_photo: UploadFile = File(...),
back_photo: UploadFile = File(...),
):
    """
    Accepts three photos (front, side, back) and a goals string.
    Save the photos to a temp local path, uploads them to GCS,
    writes a metadata JSON to GCS and returns gs:// paths.
    """
    if not GCS_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME is not configured on the server.")
    
    uid=str(uuid4())
    tmp_dir = "/tmp/uploads" 
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        #Save the uploaded files to /tmp
        front_tmp = os.path.join(tmp_dir, f"{uid}_front.jpg")
        side_tmp = os.path.join(tmp_dir, f"{uid}_side.jpg")
        back_tmp = os.path.join(tmp_dir, f"{uid}_back.jpg")

        with open(front_tmp, "wb") as f:
            shutil.copyfileobj(front_photo.file, f)
        with open(side_tmp, "wb") as f:
            shutil.copyfileobj(side_photo.file, f)
        with open(back_tmp, "wb") as f:
            shutil.copyfileobj(back_photo.file, f)

        logger.info("Saved uploaded files to rmp: %s, %s, %s", front_tmp, side_tmp, back_tmp)

        #Upload to GCS
        front_blob = f"{uid}/front.jpg"
        side_blob = f"{uid}/side.jpg"
        back_blob = f"{uid}/back.jpg"
        front_gs_path = upload_file_to_gcs(front_tmp, front_blob)
        side_gs_path = upload_file_to_gcs(side_tmp, side_blob)
        back_gs_path = upload_file_to_gcs(back_tmp, back_blob)

        logger.info("Uploaded files to GCS: %s, %s, %s", front_gs_path, side_gs_path, back_gs_path)

        #Write metadata JSON to GCS
        metadata = {
            "goals": goals,
            "uid": uid,
            "front_blob": front_blob,
            "side_blob": side_blob,
            "back_blob": back_blob,
        }
        metadata_local = os.path.join(tmp_dir, f"{uid}_metadata.json")
        with open(metadata_local, "w") as mf:
            json.dump(metadata, mf)

        metadata_blob = f"{uid}/metadata.json"
        metadata_gs_path = upload_file_to_gcs(metadata_local, metadata_blob)
        logger.info("Uploaded metadata to GCS: %s", metadata_gs_path)

        #Cleanup local temp files
        try:
            os.remove(front_tmp)
            os.remove(side_tmp)
            os.remove(back_tmp)
            os.remove(metadata_local)
        except Exception:
            logger.debug("Failed to clean up com tmp files; continuing anyway.")

        return {
            "plan_id": uid,
            "front_gs_path": front_gs_path,
            "side_gs_path": side_gs_path,
            "back_gs_path": back_gs_path,
            "metadata_gs_path": metadata_gs_path,
            "message": "Files uploaded successfully. Plan generation not implemented in this MVP."
        
        }
    
    except Exception as e:
        logger.exception("Failed during upload flow")
        raise HTTPException(status_code=500, detail=f"Upload Failed: {str(e)}")