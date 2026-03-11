#app/gcs.py small cloud storage helper for uploading files to GCS
from google.cloud import storage
import os
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _get_bucket():
    """
    Internal helper to get a client and bucket object.
    Uses a cache to ensure it's only created once per process.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME environment variable is not set.")
        raise ValueError("GCS_BUCKET_NAME is not configured.")
    
    client = storage.Client()
    return client.bucket(bucket_name)


def upload_file_to_gcs(local_filepath: str, destination_blob_name: str) -> str:
    """Uploads a file to Google Cloud Storage and returns the gs:// path."""
    bucket = _get_bucket()
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_filepath)
    logger.info(f"Uploaded {local_filepath} to gs://{bucket.name}/{destination_blob_name}")
    return f"gs://{bucket.name}/{destination_blob_name}"

def download_file_from_gcs(source_blob_name: str, local_destination: str):
    """Downloads a file from Google Cloud Storage to a local path."""
    bucket = _get_bucket()
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(local_destination)
    logger.info(f"Downloaded gs://{bucket.name}/{source_blob_name} to {local_destination}")