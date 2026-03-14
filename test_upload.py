import pytest
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

    response = client.post(
        "/submit-assessment",
        data={"goals": "test goals"},
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
        data={"goals": "test goals"},
        files={
            "front_photo": ("front.jpg", b"fake data", "image/jpeg"),
            "side_photo": ("side.png", b"fake data", "image/png"),
            "back_photo": ("hacker.exe", b"malicious code", "application/x-msdownload"),
        },
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main(["-v", "test_upload.py"])
