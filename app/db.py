import logging
from typing import Optional
from google.cloud import firestore

logger = logging.getLogger(__name__)

# Lazy-loaded global Firestore client
_db = None

def get_db() -> firestore.Client:
    global _db
    if _db is None:
        try:
            _db = firestore.Client(database="agentic-fitness-mvp-database")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            raise
    return _db

def create_assessment(plan_id: str, metadata: dict):
    db = get_db()
    doc_ref = db.collection("assessments").document(plan_id)
    doc_ref.set({
        "status": "PENDING",
        "metadata": metadata,
        "created_at": firestore.SERVER_TIMESTAMP
    })

def update_assessment_status(plan_id: str, status: str, **kwargs):
    db = get_db()
    doc_ref = db.collection("assessments").document(plan_id)
    update_data = {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}
    update_data.update(kwargs)
    doc_ref.update(update_data)

def get_assessment_doc(plan_id: str) -> Optional[dict]:
    db = get_db()
    doc_ref = db.collection("assessments").document(plan_id)
    doc = doc_ref.get()
    if doc.exists:  # type: ignore
        return doc.to_dict()  # type: ignore
    return None