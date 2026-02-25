#app/gcs.py small cloud storage helper for uploading files to GCS
from google.cloud import storage
import os

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME") # set this in your environment variables for Cloud Run

client = storage.Client()

def upload_file_to_gcs(local_filepath: str, destination_blob_name: str) -> str:
    #Uploads a file to Google Cloud Storage and returns the public URL.
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_filepath)
    # Make the file private (default) or public as needed. Here we keep it private.
    return f"gs://{BUCKET_NAME}/{destination_blob_name}"