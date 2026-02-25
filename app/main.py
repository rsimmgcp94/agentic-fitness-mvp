from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from uuid import uuid4
import shutil
import os

app = FastAPI(title="Agentic Fitness MVP")

class PlanResponse(BaseModel):
    plan_id: str
    message: str

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
    uid=str(uuid4()) 
    os.makedirs("/tmp/uploads", exist_ok=True)
    front_path = f"/tmp/uploads/{uid}_front.jpg"
    side_path = f"/tmp/uploads/{uid}_side.jpg"
    back_path = f"/tmp/uploads/{uid}_back.jpg"
    with open(front_path, "wb") as f:
        shutil.copyfileobj(front_photo.file, f)
    with open(side_path, "wb") as f:
        shutil.copyfileobj(side_photo.file, f)
    with open(back_path, "wb") as f:
        shutil.copyfileobj(back_photo.file, f)

    # Stubbed response - in a real implementation, you'd process the photos and goals to generate a plan (replace run_agent call later)
    message = "Assessment received. Agent plan generation is queued (MVP stubbed)."
    return {"plan_id": uid, "message": message}