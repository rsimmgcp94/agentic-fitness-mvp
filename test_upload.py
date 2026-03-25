import pytest # type: ignore
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_submit_assessment_valid_files(monkeypatch):
    # Mock the GCS functions to avoid actual uploads
    import app.main
    import uuid

    # We use monkeypatch to avoid actual GCS or async tasks
    def mock_upload(*args, **kwargs):
        return f"gs://mocked-bucket/{uuid.uuid4()}/mock.jpg"

    monkeypatch.setattr(app.main, "upload_file_to_gcs", mock_upload)
    monkeypatch.setattr(app.main, "create_assessment", lambda x, y: None)

    response = client.post(
        "/submit-assessment",
        data={"goals": "test goals", "age": "30", "height": "5'10\"", "weight": "180 lbs"},
        files={
            "front_photo": ("front.jpg", b"fake data", "image/jpeg"),
            "side_photo": ("side.png", b"fake data", "image/png"),
            "back_photo": ("back.webp", b"fake data", "image/webp"),
        },
    )

    assert response.status_code == 200
    assert "plan_id" in response.json()


def test_submit_assessment_invalid_file(monkeypatch):
    response = client.post(
        "/submit-assessment",
        data={"goals": "test goals", "age": "30", "height": "5'10\"", "weight": "180 lbs"},
        files={
            "front_photo": ("front.jpg", b"fake data", "image/jpeg"),
            "side_photo": ("side.png", b"fake data", "image/png"),
            "back_photo": ("hacker.exe", b"malicious code", "application/x-msdownload"),
        },
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_get_assessment_completed(monkeypatch):
    import app.main

    def mock_read_text(blob_name):
        if "plan.md" in blob_name:
            return "## Your Workout Plan"
        return None

    def mock_get_doc(plan_id):
        return {"status": "COMPLETED"}

    monkeypatch.setattr(app.main, "read_text_from_gcs", mock_read_text)
    monkeypatch.setattr(app.main, "get_assessment_doc", mock_get_doc)

    response = client.get("/assessment/test-123")
    assert response.status_code == 200
    assert response.json() == {
        "plan_id": "test-123",
        "status": "completed",
        "plan": "## Your Workout Plan"
    }


def test_get_assessment_processing(monkeypatch):
    import app.main

    def mock_get_doc(plan_id):
        return {"status": "PROCESSING"}

    monkeypatch.setattr(app.main, "get_assessment_doc", mock_get_doc)

    response = client.get("/assessment/test-456")
    assert response.status_code == 200
    assert response.json() == {"plan_id": "test-456", "status": "processing"}


def test_get_assessment_not_found(monkeypatch):
    import app.main
    monkeypatch.setattr(app.main, "get_assessment_doc", lambda x: None)

    response = client.get("/assessment/test-789")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main(["-v", "test_upload.py"])
