# Sports Media Protection

FastAPI service for multi-layer sports media piracy detection, ownership proof, risk prediction, decisioning, and dashboard analytics.

## Integrated End-to-End Pipeline

The system is now fully integrated with automatic data flow between layers:

1. **Layer 1-2**: Content Protection (DRM + Watermark + Fingerprint)
   - Upload media file via `/process` endpoint
   - Applies encryption, watermarking, and generates fingerprint
   - Automatically forwards to Layer 3-4

2. **Layer 3-4**: Ownership + Intelligence
   - Registers content ownership on blockchain
   - Generates AI feature vectors
   - Automatically triggers Layer 5-6 detection

3. **Layer 5-6**: Detection System
   - Crawls internet for potential piracy
   - Downloads short video clips
   - Extracts fingerprints and matches against reference
   - Uses AI for semantic similarity detection
   - Automatically forwards detections to Decision Engine

4. **Layer 7+**: Decision + Execution
   - Analyzes detections and makes automated decisions
   - Sends alerts and executes takedown actions
   - Provides dashboard analytics

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start all services:
   ```bash
   python run_all.py
   ```

3. Run the integrated pipeline:
   ```bash
   python integrated_pipeline.py path/to/media/file.mp4
   ```

## API Endpoints

- **Layer 1-2**: `http://127.0.0.1:8001/process` (POST file upload)
- **Main App**: `http://127.0.0.1:8000`
  - `/api/v1/layers/3-4/process` (Layer 3-4 processing)
  - `/api/v1/layer56/scan` (Layer 5-6 detection)
  - `/api/v1/decision/process` (Decision engine)
  - `/api/v1/dashboard/*` (Analytics)

## Data Flow

```
Media File
    ↓
Layer 1-2 (Protection)
    ↓ (fingerprint_hash, watermark_id, metadata)
Layer 3-4 (Ownership)
    ↓ (blockchain_tx, feature_vector, ownership_verified)
Layer 5-6 (Detection)
    ↓ (detections with similarity, verdict, risk, action)
Decision Engine (Actions)
```

## Output Format

Detection results include:

```json
{
  "url": "https://example.com/video",
  "similarity": 0.82,
  "verdict": "SUSPICIOUS",
  "risk": "MEDIUM",
  "action": "MONITOR",
  "watermark_id": "user_456",
  "ownership_verified": true
}
```

## Layer Mapping

### Layer 1-2 (Input Contracts)
- Input model source: app/models/schemas.py
- Main incoming contract: Layer12Input

### Layer 3-4 (Ownership + Feature Pipeline)
- API: app/api/routes.py
- Services: app/services/blockchain_service.py, app/services/feature_service.py, app/services/pipeline_service.py, app/services/repository.py
- Output contract: Layer34Output

### Layer 5-6 (Crawler + Matching + AI Detection)
- API: app/api/layer56.py
- Services: app/services/crawler_service.py, app/services/fingerprint_service.py, app/services/matcher_service.py, app/services/ai_engine_service.py, app/services/layer56_service.py
- Output contracts: Layer56DetectionResult, Layer56Response

### Layer 7-12 (Prediction + Leak + Decision + Execution + Dashboard)
- APIs: app/api/decision.py, app/api/dashboard.py
- Services: app/services/predictor.py, app/services/leak_identifier.py, app/services/decision_engine.py, app/services/alert_service.py, app/services/executor.py
- Database models and dependency: app/database.py

## Root Structure

```text
app/
  api/
    routes.py
    layer56.py
    decision.py
    dashboard.py
  models/
    schemas.py
  services/
    blockchain_service.py
    feature_service.py
    pipeline_service.py
    repository.py
    crawler_service.py
    fingerprint_service.py
    matcher_service.py
    ai_engine_service.py
    layer56_service.py
    predictor.py
    leak_identifier.py
    decision_engine.py
    alert_service.py
    executor.py
  config.py
  database.py
  main.py
data/
tests/
requirements.txt
README.md
```

## Setup (Using venv)

Keep virtual environment and requirements file at project root.

```bash
venv\Scripts\python.exe -m pip install -r requirements.txt
```

If venv is not created yet:

```bash
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run Service

```bash
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Docs:
- http://127.0.0.1:8000/docs

## Main Endpoints

- GET /api/v1/health
- POST /api/v1/layers/3-4/process
- GET /api/v1/layers/3-4/content/{content_id}
- POST /api/v1/layer56/scan
- GET /api/v1/layer56/scan/{content_id}
- POST /api/v1/decision/process
- GET /api/v1/dashboard/summary
- GET /api/v1/dashboard/detections?page=1&limit=20
- GET /api/v1/dashboard/alerts/{owner_id}
- GET /api/v1/dashboard/predictions
- GET /api/v1/dashboard/decisions

## Verification

```bash
venv\Scripts\python.exe tests/test_layer56_integration.py
```

## Notes

- No need to move requirements.txt into venv.
- Keep venv outside source control.
- Runtime temp files are stored in data/temp and should be ignored in git.
