# 🛡️ AI Content Protection System

A **real, working** backend + frontend system that protects media content through three layers:

| Layer | What it does | Tech |
|-------|-------------|------|
| 🔐 **DRM Encryption** | AES-128 HLS encryption of video/audio segments | FFmpeg |
| 💧 **Invisible Watermark** | DWT-based imperceptible watermark in video frames / audio waveform | OpenCV, PyWavelets |
| 🧬 **Fingerprinting** | Perceptual hash fingerprint robust to resize/compression | imagehash, librosa |

---

## 📁 Project Structure

```
AI_Solution/
├── backend/
│   ├── app.py                  # FastAPI application (main entry point)
│   ├── config.py               # All configurable paths & parameters
│   ├── requirements.txt        # Python dependencies
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── drm.py              # DRM / AES-128 HLS encryption
│   │   ├── watermark.py        # Invisible DWT watermarking
│   │   └── fingerprint.py      # Perceptual fingerprint generation
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Shared utilities (keygen, hashing, ffprobe)
├── frontend/
│   ├── index.html              # Upload UI
│   ├── style.css               # Premium dark theme
│   └── script.js               # API integration & pipeline visualisation
├── uploads/                    # Auto-created — uploaded raw files
├── outputs/                    # Auto-created — encrypted/watermarked/fingerprinted files
└── README.md                   # ← You are here
```

---

## ⚙️ Prerequisites

| Tool | Required | How to install |
|------|----------|---------------|
| **Python 3.10+** | ✅ | https://www.python.org/downloads/ |
| **FFmpeg** | ✅ | https://ffmpeg.org/download.html — **must be on PATH** |
| **pip** | ✅ | Comes with Python |
| **VS Code** | Recommended | https://code.visualstudio.com/ |

### Verify FFmpeg is installed

```bash
ffmpeg -version
ffprobe -version
```

If not found, download FFmpeg, extract it, and add its `bin/` folder to your system PATH.

---

## 🚀 Step-by-Step Setup (VS Code)

### 1. Clone / Open the project

```bash
# Open VS Code, then: File → Open Folder → select AI_Solution/
```

### 2. Create a Python virtual environment

Open a terminal in VS Code (`Ctrl + `` `) and run:

```bash
cd backend
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `opencv-python-headless` is used (no GUI needed). If you have issues, try `pip install opencv-python` instead.

### 4. Start the backend

```bash
python app.py
```

You should see:

```
============================================================
  AI Content Protection System
  http://0.0.0.0:8000
  Docs:  http://localhost:8000/docs
============================================================
```

The API is now running at **http://localhost:8000**. Open http://localhost:8000/docs for the interactive Swagger UI.

### 5. Open the frontend

Just open `frontend/index.html` in your browser:

- **Option A:** Right-click `index.html` in VS Code → *Open with Live Server* (if you have the extension)
- **Option B:** Double-click `frontend/index.html` in File Explorer
- **Option C:** Use Python's built-in server:

```bash
cd frontend
python -m http.server 3000
# Then open http://localhost:3000
```

### 6. Use the system

1. The header should show **API Online** (green dot).
2. Drag & drop a video (`.mp4`, `.mkv`) or audio (`.mp3`, `.wav`) file.
3. Optionally fill in Content ID, Owner ID, User ID.
4. Click **Protect Content**.
5. Wait for the pipeline to complete — you'll see the full JSON output.

---

## 🔧 Configuration

### Change API URL (Frontend → Backend)

Edit `frontend/script.js`, line 7:

```javascript
const API_BASE_URL = "http://localhost:8000";
```

Change this if your backend runs on a different host or port.

### Change upload/output paths

Edit `backend/config.py`:

```python
UPLOAD_DIR = PROJECT_ROOT / "uploads"    # where uploaded files are saved
OUTPUT_DIR = PROJECT_ROOT / "outputs"    # where processed files are saved
```

### Change FFmpeg path

If FFmpeg is not on PATH, set the full path in `backend/config.py`:

```python
FFMPEG_BIN = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE_BIN = r"C:\ffmpeg\bin\ffprobe.exe"
```

Or use environment variables:

```bash
set FFMPEG_BIN=C:\ffmpeg\bin\ffmpeg.exe
set FFPROBE_BIN=C:\ffmpeg\bin\ffprobe.exe
```

### Watermark strength

```python
WATERMARK_STRENGTH = 0.05   # higher = more robust but slightly more visible
```

---

## 📡 API Reference

### `POST /process`

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | Video or audio file |
| `content_id` | string | ❌ | Unique ID (auto-generated if empty) |
| `owner_id` | string | ❌ | Owner identifier (default: `owner_default`) |
| `user_id` | string | ❌ | User ID for dynamic watermarking |
| `device_info` | string | ❌ | Device/region info |

### Sample cURL Request

```bash
curl -X POST http://localhost:8000/process \
  -F "file=@sample_video.mp4" \
  -F "content_id=movie_001" \
  -F "owner_id=studio_xyz" \
  -F "user_id=user_42" \
  -F "device_info=Windows/Chrome"
```

### Sample Response

```json
{
  "content_id": "movie_001",
  "encrypted_media_path": "D:\\AI_Solution\\outputs\\movie_001\\drm",
  "drm_license_info": {
    "license_server_url": "http://localhost:8000/drm/keys/movie_001",
    "key_id": "a1b2c3d4e5f6...",
    "encryption_scheme": "AES-128-CBC",
    "key_delivery": "clear-key (simulated)",
    "note": "In production, replace this with a Widevine/FairPlay/PlayReady license server endpoint."
  },
  "watermark_id": "f3a8c1d9e7b20415",
  "watermarked_media_path": "D:\\AI_Solution\\outputs\\movie_001\\watermarked\\watermarked_sample_video.mp4",
  "fingerprint_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "metadata": {
    "owner_id": "studio_xyz",
    "user_id": "user_42",
    "device_info": "Windows/Chrome",
    "timestamp": "2026-04-27T14:45:00+00:00",
    "processing_logs": "[PIPELINE] content_id=movie_001\n[DRM] Started at ...\n..."
  }
}
```

### Other Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger interactive docs |

---

## 🐛 Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ffmpeg: not found` / `'ffmpeg' is not recognized` | FFmpeg not installed or not on PATH | Install FFmpeg and add to PATH, or set `FFMPEG_BIN` in `config.py` |
| `ModuleNotFoundError: No module named 'cv2'` | OpenCV not installed | `pip install opencv-python-headless` |
| `uvicorn: not recognized` | uvicorn not installed | `pip install uvicorn` or run `python app.py` instead |
| `API Offline` in frontend | Backend not running or wrong URL | Start backend with `python app.py`, check `API_BASE_URL` in `script.js` |
| `CORS error` in browser console | Cross-origin blocked | Backend already allows `*` origins. Use a local server for the frontend instead of `file://` |
| `Permission denied` on uploads/outputs | Directory permission issue | Run as administrator or change paths in `config.py` |
| Large file timeout | File too big for default timeout | Increase `timeout` in `helpers.py run_cmd()` |
| `No audio in watermarked video` | FFmpeg audio codec issue | Install full FFmpeg build with AAC support |

---

## 🧪 How Each Module Works

### 🔐 DRM (drm.py)

1. Generates a random **AES-128 key** (16 bytes).
2. Creates an HLS **key-info file** with the key, URI, and IV.
3. Runs **FFmpeg** to segment the video into `.ts` chunks, encrypted with AES-128-CBC.
4. Outputs an `.m3u8` manifest and encrypted segments.
5. Returns simulated **license server metadata** (in production, this would be Widevine/FairPlay/PlayReady).

### 💧 Watermark (watermark.py)

1. Reads each frame with **OpenCV**.
2. Converts to **YCrCb** colour space (isolates luminance).
3. Applies **2-level Haar DWT** (Discrete Wavelet Transform) via PyWavelets.
4. Encodes the watermark string as binary bits.
5. Embeds bits into the **LL2 sub-band** coefficients (imperceptible changes).
6. Reconstructs frames via inverse DWT.
7. Re-muxes audio from the original file via FFmpeg.

### 🧬 Fingerprint (fingerprint.py)

**Video:**
1. Samples N evenly-spaced frames.
2. Computes 4 perceptual hashes per frame: **aHash, pHash, dHash, wHash**.
3. Combines all hashes via **SHA-256** into a single composite fingerprint.

**Audio:**
1. Computes **Mel-spectrogram** and **chromagram** via librosa.
2. Quantizes and hashes both.
3. Combines via **SHA-256**.

---

## 🔮 Next Steps (AI Detection Layer)

The JSON output from this system feeds into the next layer:

```
Protected Content + Metadata JSON
        ↓
  AI Detection Layer
  ├── Internet Crawling Engine
  ├── Fingerprint Matching (compare against database)
  ├── Watermark Extraction (trace leak source)
  ├── Predictive Piracy AI
  └── DMCA / Takedown Automation
```

---

## 📜 License

This project is a prototype/hackathon submission. Use responsibly.
