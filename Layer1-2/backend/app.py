"""
Content Protection System — FastAPI Backend
=============================================
Single API endpoint: POST /process
Accepts media + metadata, runs the full protection pipeline:
  1. DRM Encryption (AES-128 HLS)
  2. Invisible Watermarking (DWT)
  3. Fingerprint Generation (perceptual hashing)
Returns structured JSON with all outputs and metadata.
"""

import sys
import uuid
import traceback
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import httpx

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    UPLOAD_DIR,
    OUTPUT_DIR,
    API_HOST,
    API_PORT,
    CORS_ORIGINS,
)
from modules.drm import encrypt_media
from modules.watermark import embed_watermark
from modules.fingerprint import generate_fingerprint
from utils.helpers import now_iso

# ──────────────────────────────────────────────────────────────────────
#  App setup
# ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Content Protection System",
    description="DRM Encryption → Invisible Watermarking → Fingerprint Generation",
    version="1.0.0",
)

# CORS — allow the frontend (and any origin during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the outputs folder so encrypted segments are downloadable
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/ui")
async def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


# ──────────────────────────────────────────────────────────────────────
#  Health check
# ──────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "AI Content Protection System",
        "endpoints": {
            "POST /process": "Upload & protect media",
            "GET /health": "Health check",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": now_iso()}


# ──────────────────────────────────────────────────────────────────────
#  Main processing endpoint
# ──────────────────────────────────────────────────────────────────────

@app.post("/process")
async def process_media(
    file: UploadFile = File(..., description="Video or audio file to protect"),
    content_id: str = Form(default="", description="Unique content identifier (auto-generated if empty)"),
    owner_id: str = Form(default="owner_default", description="Content owner identifier"),
    user_id: str = Form(default="", description="Optional user ID for dynamic watermarking"),
    device_info: str = Form(default="", description="Optional device/region info"),
):
    """
    **Full Content Protection Pipeline**

    1. Saves the uploaded file.
    2. Runs DRM encryption (AES-128 HLS via FFmpeg).
    3. Embeds an invisible DWT watermark.
    4. Generates a perceptual fingerprint.
    5. Returns structured JSON with all paths and metadata.
    """
    upload_timestamp = now_iso()
    processing_logs: list[str] = []

    # ── Auto-generate content_id if not provided ─────────────────────
    if not content_id.strip():
        content_id = f"cid_{uuid.uuid4().hex[:12]}"

    processing_logs.append(f"[PIPELINE] content_id={content_id}")
    processing_logs.append(f"[PIPELINE] owner_id={owner_id}")
    processing_logs.append(f"[PIPELINE] upload_timestamp={upload_timestamp}")

    # ── 1. Save uploaded file ────────────────────────────────────────
    content_upload_dir = UPLOAD_DIR / content_id
    content_upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = content_upload_dir / file.filename
    try:
        with open(saved_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                f.write(chunk)
        processing_logs.append(f"[PIPELINE] File saved: {saved_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    input_path = str(saved_path)

    # ── 2. DRM Encryption ────────────────────────────────────────────
    drm_result = {}
    try:
        drm_result = encrypt_media(input_path, content_id, owner_id)
        processing_logs.append(drm_result.get("processing_log", ""))
        processing_logs.append("[PIPELINE] ✅ DRM encryption complete")
    except Exception as e:
        processing_logs.append(f"[PIPELINE] ⚠️ DRM encryption failed: {e}")
        processing_logs.append(traceback.format_exc())
        drm_result = {
            "encrypted_media_path": "",
            "drm_license_info": {"error": str(e)},
            "processing_log": f"DRM FAILED: {e}",
        }

    # ── 3. Invisible Watermarking ────────────────────────────────────
    wm_result = {}
    watermark_text = f"CPS:{content_id}:{owner_id}"
    try:
        wm_result = embed_watermark(
            input_path, content_id, watermark_text, owner_id, user_id
        )
        processing_logs.append(wm_result.get("processing_log", ""))
        processing_logs.append("[PIPELINE] ✅ Watermark embedding complete")
    except Exception as e:
        processing_logs.append(f"[PIPELINE] ⚠️ Watermark embedding failed: {e}")
        processing_logs.append(traceback.format_exc())
        wm_result = {
            "watermarked_media_path": "",
            "watermark_id": "",
            "processing_log": f"WATERMARK FAILED: {e}",
        }

    # ── 4. Fingerprint Generation ────────────────────────────────────
    fp_result = {}
    try:
        fp_result = generate_fingerprint(input_path, content_id)
        processing_logs.append(fp_result.get("processing_log", ""))
        processing_logs.append("[PIPELINE] ✅ Fingerprint generation complete")
    except Exception as e:
        processing_logs.append(f"[PIPELINE] ⚠️ Fingerprint generation failed: {e}")
        processing_logs.append(traceback.format_exc())
        fp_result = {
            "fingerprint_hash": "",
            "processing_log": f"FINGERPRINT FAILED: {e}",
        }

    # ── 5. Build final response ──────────────────────────────────────
    response = {
        "content_id": content_id,
        "encrypted_media_path": drm_result.get("encrypted_media_path", ""),
        "drm_license_info": drm_result.get("drm_license_info", {}),
        "watermark_id": wm_result.get("watermark_id", ""),
        "watermarked_media_path": wm_result.get("watermarked_media_path", ""),
        "fingerprint_hash": fp_result.get("fingerprint_hash", ""),
        "metadata": {
            "owner_id": owner_id,
            "user_id": user_id,
            "device_info": device_info,
            "timestamp": upload_timestamp,
            "processing_logs": "\n".join(processing_logs),
        },
    }

    # Persist the full result JSON alongside outputs
    result_json_path = OUTPUT_DIR / content_id / "protection_result.json"
    result_json_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    result_json_path.write_text(json.dumps(response, indent=2))

    # Auto-forward to Layer 3+4
    layer34_payload = {
        "content_id": response["content_id"],
        "encrypted_media_path": response["encrypted_media_path"],
        "drm_license_info": str(response["drm_license_info"]),
        "watermark_id": response["watermark_id"],
        "fingerprint_hash": response["fingerprint_hash"],
        "metadata": response["metadata"],
    }

    try:
        layer34_url = os.getenv("LAYER34_API_URL", "http://127.0.0.1:8000")
        httpx.post(
            f"{layer34_url}/api/v1/layers/3-4/process",
            json=layer34_payload,
            timeout=10.0,
        )
    except Exception:
        pass  # don't fail if Layer 3+4 is not running

    return JSONResponse(content=response)


# ──────────────────────────────────────────────────────────────────────
#  Serve frontend static assets (CSS, JS) — must be AFTER all routes
# ──────────────────────────────────────────────────────────────────────
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_static")


# ──────────────────────────────────────────────────────────────────────
#  Run with: python app.py
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  AI Content Protection System")
    print(f"  http://{API_HOST}:{API_PORT}")
    print(f"  Docs:  http://localhost:{API_PORT}/docs")
    print("=" * 60)
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True)
