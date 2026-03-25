import time
import os
import json
import shutil
import cv2
import numpy as np

# Mock GCS functions
def mock_download_file_from_gcs(source_blob_name, local_destination):
    time.sleep(0.5) # Simulate network delay
    # Create a dummy image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(local_destination, img)

def mock_upload_file_to_gcs(local_filepath, destination_blob_name):
    time.sleep(0.1)
    return f"gs://mocked-bucket/{destination_blob_name}"

def mock_generate_workout_plan(*args, **kwargs):
    time.sleep(1.0)
    return "Mocked plan"

import app.main
app.main.download_file_from_gcs = mock_download_file_from_gcs
app.main.upload_file_to_gcs = mock_upload_file_to_gcs
app.main.generate_workout_plan = mock_generate_workout_plan

from fastapi.testclient import TestClient

os.environ["GCS_BUCKET_NAME"] = "mocked-bucket"

client = TestClient(app.main.app)

def run_benchmark():
    # Setup mock metadata
    uid = "test_perf_uid"
    tmp_dir = f"/tmp/{uid}_processing"
    os.makedirs(tmp_dir, exist_ok=True)

    metadata = {
        "goals": "get fit",
        "front_blob": f"{uid}/front.jpg",
        "side_blob": f"{uid}/side.jpg",
        "back_blob": f"{uid}/back.jpg"
    }

    def override_download(source_blob_name, local_destination):
        if source_blob_name.endswith("metadata.json"):
            with open(local_destination, "w") as f:
                json.dump(metadata, f)
        else:
            mock_download_file_from_gcs(source_blob_name, local_destination)

    app.main.download_file_from_gcs = override_download

    start_time = time.time()

    payload = {
        "plan_id": uid,
        "metadata_gs_path": f"gs://mocked-bucket/{uid}/metadata.json"
    }

    response = client.post("/worker/process-assessment", json=payload)
    end_time = time.time()

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    else:
        print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == '__main__':
    run_benchmark()
