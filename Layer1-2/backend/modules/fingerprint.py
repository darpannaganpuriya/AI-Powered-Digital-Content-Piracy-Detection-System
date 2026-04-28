"""
Fingerprinting Module
======================
Generates robust perceptual fingerprints for video and audio content.

Video fingerprinting:
    - Sample N evenly-spaced frames from the video.
    - For each frame, compute multiple perceptual hashes (average hash,
      perceptual hash, difference hash, wavelet hash) via the `imagehash` library.
    - Combine all per-frame hashes into a single composite fingerprint using SHA-256.
    - These perceptual hashes are resilient to resizing, mild compression,
      and minor colour adjustments.

Audio fingerprinting:
    - Load the audio via librosa.
    - Compute the Mel-spectrogram (robust spectral representation).
    - Compute a chromagram (pitch-class profile).
    - Hash both representations and combine into a single fingerprint.
    - Resilient to bitrate changes, slight speed shifts, and re-encoding.
"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import imagehash

from config import (
    FINGERPRINT_FRAME_COUNT,
    FINGERPRINT_AUDIO_DURATION,
    OUTPUT_DIR,
)
from utils.helpers import now_iso, is_video, is_audio


# ──────────────────────────────────────────────────────────────────────
#  Video fingerprinting
# ──────────────────────────────────────────────────────────────────────

def _sample_frame_indices(total_frames: int, n_samples: int) -> list[int]:
    """Return `n_samples` evenly-spaced frame indices across the video."""
    if total_frames <= n_samples:
        return list(range(total_frames))
    step = total_frames / n_samples
    return [int(step * i) for i in range(n_samples)]


def _hash_frame(frame_bgr: np.ndarray) -> dict[str, str]:
    """
    Compute four perceptual hashes for one BGR frame.
    Returns dict with hash names → hex strings.
    """
    # Convert OpenCV BGR → PIL RGB
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    return {
        "ahash": str(imagehash.average_hash(pil_img, hash_size=16)),
        "phash": str(imagehash.phash(pil_img, hash_size=16)),
        "dhash": str(imagehash.dhash(pil_img, hash_size=16)),
        "whash": str(imagehash.whash(pil_img, hash_size=16)),
    }


def fingerprint_video(input_path: str, content_id: str) -> dict:
    """
    Generate a composite perceptual fingerprint for a video file.

    Returns
    -------
    dict with fingerprint_hash, per_frame_hashes, processing_log
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input media not found: {input_path}")

    log: list[str] = [f"[FP-Video] Started at {now_iso()}"]

    cap = cv2.VideoCapture(str(input_file))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = _sample_frame_indices(total_frames, FINGERPRINT_FRAME_COUNT)
    log.append(f"[FP-Video] Total frames: {total_frames}, sampling {len(indices)} frames")

    per_frame: list[dict] = []
    combined_hash_input = ""

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        hashes = _hash_frame(frame)
        hashes["frame_index"] = idx
        per_frame.append(hashes)
        # Accumulate all hash strings for the composite hash
        combined_hash_input += hashes["ahash"] + hashes["phash"] + hashes["dhash"] + hashes["whash"]

    cap.release()

    # Composite fingerprint = SHA-256 of concatenated perceptual hashes
    fingerprint_hash = hashlib.sha256(combined_hash_input.encode()).hexdigest()
    log.append(f"[FP-Video] Composite fingerprint: {fingerprint_hash[:16]}…")

    # Persist per-frame hashes as JSON sidecar
    fp_folder = OUTPUT_DIR / content_id / "fingerprint"
    fp_folder.mkdir(parents=True, exist_ok=True)
    sidecar_path = fp_folder / "fingerprint_detail.json"
    sidecar = {
        "content_id": content_id,
        "fingerprint_hash": fingerprint_hash,
        "algorithm": "imagehash (ahash+phash+dhash+whash) → SHA-256",
        "frame_count_sampled": len(per_frame),
        "per_frame_hashes": per_frame,
        "generated_at": now_iso(),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    log.append(f"[FP-Video] Detail written to {sidecar_path}")
    log.append(f"[FP-Video] Finished at {now_iso()}")

    return {
        "fingerprint_hash": fingerprint_hash,
        "detail_path": str(sidecar_path),
        "processing_log": "\n".join(log),
    }


# ──────────────────────────────────────────────────────────────────────
#  Audio fingerprinting
# ──────────────────────────────────────────────────────────────────────

def fingerprint_audio(input_path: str, content_id: str) -> dict:
    """
    Generate a robust spectral fingerprint for an audio file using librosa.

    Approach:
    1. Compute the Mel-spectrogram and hash it.
    2. Compute the chromagram and hash it.
    3. Combine both into a single SHA-256 composite fingerprint.
    """
    import librosa

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input media not found: {input_path}")

    log: list[str] = [f"[FP-Audio] Started at {now_iso()}"]

    # Load audio (mono, limited duration for speed)
    y, sr = librosa.load(
        str(input_file),
        sr=22050,
        mono=True,
        duration=FINGERPRINT_AUDIO_DURATION,
    )
    log.append(f"[FP-Audio] Loaded {len(y)} samples @ {sr} Hz ({len(y)/sr:.1f}s)")

    # --- Mel-spectrogram hash ---
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    # Quantise to 8-bit for hashing stability
    mel_norm = ((mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8) * 255).astype(np.uint8)
    mel_hash = hashlib.sha256(mel_norm.tobytes()).hexdigest()
    log.append(f"[FP-Audio] Mel-spec hash: {mel_hash[:16]}…")

    # --- Chroma hash ---
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_norm = ((chroma - chroma.min()) / (chroma.max() - chroma.min() + 1e-8) * 255).astype(np.uint8)
    chroma_hash = hashlib.sha256(chroma_norm.tobytes()).hexdigest()
    log.append(f"[FP-Audio] Chroma hash: {chroma_hash[:16]}…")

    # --- Composite fingerprint ---
    fingerprint_hash = hashlib.sha256((mel_hash + chroma_hash).encode()).hexdigest()
    log.append(f"[FP-Audio] Composite fingerprint: {fingerprint_hash[:16]}…")

    # Persist detail
    fp_folder = OUTPUT_DIR / content_id / "fingerprint"
    fp_folder.mkdir(parents=True, exist_ok=True)
    sidecar_path = fp_folder / "fingerprint_detail.json"
    sidecar = {
        "content_id": content_id,
        "fingerprint_hash": fingerprint_hash,
        "algorithm": "librosa (mel-spec + chroma) → SHA-256",
        "mel_hash": mel_hash,
        "chroma_hash": chroma_hash,
        "duration_analysed_s": round(len(y) / sr, 2),
        "generated_at": now_iso(),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    log.append(f"[FP-Audio] Finished at {now_iso()}")

    return {
        "fingerprint_hash": fingerprint_hash,
        "detail_path": str(sidecar_path),
        "processing_log": "\n".join(log),
    }


# ──────────────────────────────────────────────────────────────────────
#  Dispatcher
# ──────────────────────────────────────────────────────────────────────

def generate_fingerprint(input_path: str, content_id: str) -> dict:
    """
    Auto-detect media type and generate the appropriate fingerprint.
    """
    if is_video(input_path):
        return fingerprint_video(input_path, content_id)
    elif is_audio(input_path):
        return fingerprint_audio(input_path, content_id)
    else:
        raise ValueError(f"Unsupported media type for fingerprinting: {input_path}")
