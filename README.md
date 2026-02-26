```markdown
# agentic-fitness-mvp

A portfolio-focused **Agentic AI Fitness MVP** backend built with **FastAPI** and deployed on **Google Cloud Run**.  
This POC currently supports assessment submissions (goals + two photos), persists uploads to **Google Cloud Storage (GCS)**, and returns structured paths to uploaded artifacts.

**Cloud Run URL:** https://agentic-fitness-mvp-432298206863.us-central1.run.app

> Status: **Milestone A complete** (scaffold + upload persistence). No async processing, agent logic, or image analysis yet.

---

## Tech Stack

- **Python 3.11**
- **FastAPI**
- **Docker**
- **Google Cloud Run (GCP)**
- **Google Cloud Storage (GCS)**
- **GitHub Actions CI/CD** (auto redeploy on push to `main`)

---

## Live API

- Health: `GET https://agentic-fitness-mvp-432298206863.us-central1.run.app/health`
- Submit assessment: `POST https://agentic-fitness-mvp-432298206863.us-central1.run.app/submit-assessment`

---

## Current Capabilities (Milestone A)

### `GET /health`
Basic health check endpoint.

### `POST /submit-assessment`
Accepts a multipart form submission:

- `goals` (form field)
- `front_photo` (file)
- `side_photo` (file)

**Behavior**
1. Generates a UUID for the submission.
2. Temporarily writes uploads to `/tmp`.
3. Uploads files to GCS under a per-submission folder.
4. Creates and uploads `metadata.json` to GCS.
5. Cleans up local `/tmp` files.
6. Returns a JSON response with the submission id and GCS paths.

**Example response**
```

{

"id": "uuid-here",

"front_gs_path": "gs://<bucket>/<uuid>/front.jpg",

"side_gs_path": "gs://<bucket>/<uuid>/side.jpg",

"metadata_gs_path": "gs://<bucket>/<uuid>/metadata.json"

}

```

---

## Quickstart (curl)

### Health
```

curl -s https://agentic-fitness-mvp-432298206863.us-central1.run.app/health

```

### Submit an assessment
```

curl -X POST "https://agentic-fitness-mvp-432298206863.us-central1.run.app/submit-assessment" \

-F "goals=Build muscle and improve posture" \

-F "front_photo=@./front.jpg" \

-F "side_photo=@./side.jpg"

```

---

## Storage Layout (GCS)

Uploads are written to:

- `gs://<bucket>/<uuid>/front.jpg`
- `gs://<bucket>/<uuid>/side.jpg`
- `gs://<bucket>/<uuid>/metadata.json`

---

## Project Structure (Conceptual)

```

app/

[main.py](http://main.py)

[gcs.py](http://gcs.py)

requirements.txt

Dockerfile

.gitignore

.dockerignore

```

---

## Configuration

### Environment Variables

Required:

- `GCS_BUCKET=<bucket-name>`

### GCS Helper

`app/gcs.py` provides:

```

upload_file(local_path: str, dest_blob_name: str) -> str

```

---

## Local Development

### 1) Create and activate a virtual environment
```

python -m venv .venv

source .venv/bin/activate

```

### 2) Install dependencies
```

pip install -r requirements.txt

```

### 3) Run the API
```

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

```

> Ensure `GCS_BUCKET` is set and your local environment has GCP credentials that can upload to the bucket.

---

## Docker

### Build
```

docker build -t agentic-fitness-mvp .

```

### Run
```

docker run -p 8000:8000 -e GCS_BUCKET=<bucket-name> agentic-fitness-mvp

```

---

## Deployment

Deployed on **Cloud Run** and configured to **auto redeploy on push to `main`** via **GitHub Actions**.

---

## Roadmap (Planned, Not Implemented Yet)

- Async processing via **Cloud Tasks** or **Pub/Sub**
- Worker endpoint (e.g. `/work-order/{id}`)
- Image analysis (MediaPipe / MoveNet) with `analysis.json` persisted to GCS
- LLM integration
- RAG pipeline + Vector DB
- Postgres / Cloud SQL
- Structured audit logging + observability
- Signed URLs for secure frontend access
- IAM least-privilege refinement

---

## Design Intent

This project is being built as a portfolio-quality **Agentic AI system** demonstrating:

- Cloud-native architecture (Cloud Run + GCS)
- Production-style async processing (next milestone)
- Tool-based agent orchestration (future)
- Secure handling of user-uploaded data
- Infrastructure maturity (Docker, CI/CD, IAM)

Long-term direction:

**User Input → Tool Calls (Image Analysis + RAG) → LLM Agent → Structured Plan → Logged + Auditable Output**
```
