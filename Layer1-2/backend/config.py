"""
Configuration for the Content Protection System.
All paths are relative to the project root (parent of backend/).
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# Path Configuration
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # d:\AI_Solution
UPLOAD_DIR = PROJECT_ROOT / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Ensure directories exist at import time
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# FFmpeg Configuration
# ──────────────────────────────────────────────
# Set to the full path of ffmpeg/ffprobe if not on PATH
FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_BIN", "ffprobe")

# ──────────────────────────────────────────────
# DRM / Encryption Settings
# ──────────────────────────────────────────────
# AES-128 key length (16 bytes = 128 bits)
AES_KEY_LENGTH = 16
# HLS segment duration in seconds
HLS_SEGMENT_DURATION = 4

# ──────────────────────────────────────────────
# Watermark Settings
# ──────────────────────────────────────────────
# Strength of the DWT watermark embedding (higher = more robust but more visible)
WATERMARK_STRENGTH = 0.05
# Maximum number of frames to watermark (set to 0 to watermark all)
MAX_WATERMARK_FRAMES = 0
# DWT wavelet family
WAVELET = "haar"

# ──────────────────────────────────────────────
# Fingerprint Settings
# ──────────────────────────────────────────────
# Number of frames to sample for video fingerprinting
FINGERPRINT_FRAME_COUNT = 8
# Audio fingerprint – number of seconds to analyse
FINGERPRINT_AUDIO_DURATION = 30

# ──────────────────────────────────────────────
# API Settings
# ──────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8001
CORS_ORIGINS = ["*"]          # tighten in production
MAX_UPLOAD_SIZE_MB = 500
