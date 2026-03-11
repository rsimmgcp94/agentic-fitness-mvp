from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional
import shutil
import os
from functools import lru_cache
import json
import logging
from app.gcs import upload_file_to_gcs, download_file_from_gcs
from app.analysis import analyze_pose
from google.cloud import tasks_v2

#Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic-fitness-mvp")

# Read required env var
# Cloud Tasks Configuration
PROJECT_ID = os.getenv("GCP_PROJECT")
QUEUE_REGION = os.getenv("CLOUD_TASKS_LOCATION", "us-central1")
QUEUE_ID = os.getenv("CLOUD_TASKS_QUEUE", "agentic-fitness-queue")
SERVICE_URL = os.getenv("SERVICE_URL") # The public URL of this Cloud Run service

    
@lru_cache(maxsize=1)
def get_tasks_client():
    """Cached factory for the Cloud Tasks client."""
    return tasks_v2.CloudTasksClient()

app = FastAPI(title="Agentic Fitness MVP")

class PlanResponse(BaseModel):
    plan_id: str
    message: Optional[str] = None
    front_gs_path: str
    side_gs_path: str
    back_gs_path: str
    metadata_gs_path: str

class WorkerPayload(BaseModel):
    plan_id: str
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
    uid = str(uuid4())
    tmp_dir = f"/tmp/uploads/{uid}"
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        #Save the uploaded files to /tmp
        front_tmp = os.path.join(tmp_dir, "front.jpg")
        side_tmp = os.path.join(tmp_dir, "side.jpg")
        back_tmp = os.path.join(tmp_dir, "back.jpg")

        with open(front_tmp, "wb") as f:
            shutil.copyfileobj(front_photo.file, f)
        with open(side_tmp, "wb") as f:
            shutil.copyfileobj(side_photo.file, f)
        with open(back_tmp, "wb") as f:
            shutil.copyfileobj(back_photo.file, f)

        logger.info("Saved uploaded files to tmp: %s, %s, %s", front_tmp, side_tmp, back_tmp)

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
        metadata_local = os.path.join(tmp_dir, "metadata.json")
        with open(metadata_local, "w") as mf:
            json.dump(metadata, mf)

        metadata_blob = f"{uid}/metadata.json"
        metadata_gs_path = upload_file_to_gcs(metadata_local, metadata_blob)
        logger.info("Uploaded metadata to GCS: %s", metadata_gs_path)

        # Enqueue Cloud Task for Async Processing
        if PROJECT_ID and QUEUE_REGION and QUEUE_ID and SERVICE_URL:
            try:
                client = tasks_v2.CloudTasksClient()
                client = get_tasks_client()
                parent = client.queue_path(PROJECT_ID, QUEUE_REGION, QUEUE_ID)
                
                task_payload = {
                    "plan_id": uid,
                    "metadata_gs_path": metadata_gs_path
                }
                
                task = {
                    "http_request": {
                        "http_method": tasks_v2.HttpMethod.POST,
                        "url": f"{SERVICE_URL}/worker/process-assessment",
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(task_payload).encode(),
                    }
                }
                response = client.create_task(request={"parent": parent, "task": task})
                logger.info("Enqueued task: %s", response.name)
            except Exception as e:
                logger.error(f"Failed to enqueue task: {e}")
        else:
            logger.warning("Skipping Cloud Task creation: Missing configuration.")

        #Cleanup local temp files
        try:
            os.remove(front_tmp)
            os.remove(side_tmp)
            os.remove(back_tmp)
            os.remove(metadata_local)
        except Exception:
            logger.debug("Failed to clean up local tmp files; continuing anyway.")

        return {
            "plan_id": uid,
            "front_gs_path": front_gs_path,
            "side_gs_path": side_gs_path,
            "back_gs_path": back_gs_path,
            "metadata_gs_path": metadata_gs_path,
            "message": "Files uploaded successfully. Analysis task enqueued."
        }
    
    except Exception as e:
        logger.exception("Failed during upload flow")
        raise HTTPException(status_code=500, detail=f"Upload Failed: {str(e)}")
    finally:
        # Cleanup local temp directory
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

@app.post("/worker/process-assessment")
async def process_assessment(payload: WorkerPayload):
    """Worker endpoint called by Cloud Tasks."""
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    logger.info(f"Worker received task for plan_id: {payload.plan_id}")
    
    uid = payload.plan_id
    tmp_dir = f"/tmp/{uid}_processing"
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        # 1. Parse metadata blob name from gs:// path
        # Format: gs://bucket_name/blob_name
        if not payload.metadata_gs_path.startswith(f"gs://{GCS_BUCKET_NAME}/"):
            raise ValueError(f"Invalid GCS path: {payload.metadata_gs_path}")
            
        metadata_blob_name = payload.metadata_gs_path.replace(f"gs://{GCS_BUCKET_NAME}/", "")
        local_metadata_path = os.path.join(tmp_dir, "metadata.json")
        
        # 2. Download and read metadata
        download_file_from_gcs(metadata_blob_name, local_metadata_path)
        with open(local_metadata_path, "r") as f:
            metadata = json.load(f)

        # 3. Process each image
        analysis_results = {}
        for angle in ["front", "side", "back"]:
            blob_key = f"{angle}_blob"
            if blob_key in metadata:
                blob_name = metadata[blob_key]
                local_img_path = os.path.join(tmp_dir, f"{angle}.jpg")
                
                logger.info(f"Downloading {angle} image: {blob_name}")
                download_file_from_gcs(blob_name, local_img_path)
                
                logger.info(f"Analyzing {angle} image...")
                analysis_results[angle] = analyze_pose(local_img_path)

        # 4. Save analysis results
        analysis_local_path = os.path.join(tmp_dir, "analysis.json")
        with open(analysis_local_path, "w") as f:
            json.dump(analysis_results, f)
            
        # 5. Upload analysis to GCS
        analysis_blob_name = f"{uid}/analysis.json"
        analysis_gs_path = upload_file_to_gcs(analysis_local_path, analysis_blob_name)
        logger.info(f"Analysis complete. Uploaded to: {analysis_gs_path}")

        return {"status": "success", "analysis_gs_path": analysis_gs_path}

    except Exception as e:
        logger.exception(f"Worker failed for plan_id {uid}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)