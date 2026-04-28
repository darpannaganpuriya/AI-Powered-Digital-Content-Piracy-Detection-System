"""
Invisible Watermarking Module
==============================
Embeds an invisible watermark into video frames (or audio) using the
Discrete Wavelet Transform (DWT) technique.

Algorithm (video):
1. Decode the video frame-by-frame with OpenCV.
2. For each frame, convert to YCrCb colour space (luminance + chroma).
3. Apply a 2-level DWT (Haar wavelet) to the Y (luminance) channel.
4. Encode the watermark string as a binary bit-stream.
5. Embed each bit into the LL2 (low-low) sub-band coefficients by
   slightly modifying their magnitude.  The modification is controlled
   by WATERMARK_STRENGTH so the change is imperceptible.
6. Inverse-DWT → convert back to BGR → write frame to output video.

Algorithm (audio):
1. Load the audio waveform with librosa.
2. Apply DWT to the signal.
3. Embed watermark bits into the approximation coefficients.
4. Inverse-DWT → write output with soundfile.

The watermark is recoverable by comparing original vs watermarked frames
(semi-blind) or by knowing the embedding positions (this implementation
stores a small JSON sidecar with extraction hints).
"""

import json
import hashlib
import struct
from pathlib import Path

import cv2
import numpy as np
import pywt

from config import (
    FFMPEG_BIN,
    WATERMARK_STRENGTH,
    MAX_WATERMARK_FRAMES,
    WAVELET,
    OUTPUT_DIR,
)
from utils.helpers import run_cmd, now_iso, is_video, is_audio


# ──────────────────────────────────────────────────────────────────────
#  Internal helpers
# ──────────────────────────────────────────────────────────────────────

def _text_to_bits(text: str) -> list[int]:
    """Convert a UTF-8 string to a list of bits (0/1)."""
    byte_data = text.encode("utf-8")
    # Prepend 4-byte length header so we know how many bytes to extract
    length_prefix = struct.pack(">I", len(byte_data))
    full = length_prefix + byte_data
    bits = []
    for byte in full:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_text(bits: list[int]) -> str:
    """Recover a UTF-8 string from a bit list produced by _text_to_bits."""
    # First 32 bits = 4-byte length
    if len(bits) < 32:
        return ""
    length_bits = bits[:32]
    length_bytes = bytearray()
    for i in range(0, 32, 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | length_bits[i + j]
        length_bytes.append(byte_val)
    text_len = struct.unpack(">I", bytes(length_bytes))[0]

    total_bits_needed = 32 + text_len * 8
    if len(bits) < total_bits_needed:
        return ""
    text_bits = bits[32:total_bits_needed]
    text_bytes = bytearray()
    for i in range(0, len(text_bits), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | text_bits[i + j]
        text_bytes.append(byte_val)
    return bytes(text_bytes).decode("utf-8", errors="replace")


def _embed_watermark_frame(frame_y: np.ndarray, bits: list[int], strength: float) -> np.ndarray:
    """
    Embed watermark bits into a single-channel (Y) frame using 2-level DWT.
    Returns the modified Y channel.
    """
    # Ensure dimensions are even for DWT
    h, w = frame_y.shape
    h2, w2 = h - h % 2, w - w % 2
    y_crop = frame_y[:h2, :w2].astype(np.float64)

    # 2-level DWT decomposition
    coeffs = pywt.wavedec2(y_crop, WAVELET, level=2)
    # coeffs = [cA2, (cH2, cV2, cD2), (cH1, cV1, cD1)]
    ll2 = coeffs[0]  # approximation at level 2

    # Flatten LL2, embed bits cyclically
    flat = ll2.flatten()
    for i, bit in enumerate(bits):
        idx = i % len(flat)
        if bit == 1:
            flat[idx] = flat[idx] + strength * abs(flat[idx])
        else:
            flat[idx] = flat[idx] - strength * abs(flat[idx])
    coeffs[0] = flat.reshape(ll2.shape)

    # Inverse DWT
    reconstructed = pywt.waverec2(coeffs, WAVELET)
    # Clip and resize back to original
    reconstructed = np.clip(reconstructed[:h2, :w2], 0, 255).astype(np.uint8)

    # Paste back (handles odd dimensions)
    result = frame_y.copy()
    result[:h2, :w2] = reconstructed
    return result


# ──────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────

def embed_watermark_video(
    input_path: str,
    content_id: str,
    watermark_text: str,
    owner_id: str = "",
    user_id: str = "",
) -> dict:
    """
    Embed an invisible DWT watermark into every frame of a video file.

    Parameters
    ----------
    input_path    : path to source video
    content_id    : unique content identifier
    watermark_text: string to embed (e.g. content_id + user_id hash)
    owner_id      : owner identifier (stored in sidecar metadata)
    user_id       : optional per-user dynamic watermark component

    Returns
    -------
    dict with watermarked_media_path, watermark_id, sidecar_path, processing_log
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input media not found: {input_path}")

    log: list[str] = [f"[WM] Started at {now_iso()}"]

    # Prepare output paths
    wm_folder = OUTPUT_DIR / content_id / "watermarked"
    wm_folder.mkdir(parents=True, exist_ok=True)
    output_path = wm_folder / f"wm_{input_file.name}"
    sidecar_path = wm_folder / "watermark_sidecar.json"

    # Build the watermark payload
    # Combine static (content_id) and dynamic (user_id) parts
    if user_id:
        payload = f"{watermark_text}|uid:{user_id}"
    else:
        payload = watermark_text
    watermark_id = hashlib.sha256(payload.encode()).hexdigest()[:16]
    bits = _text_to_bits(payload)
    log.append(f"[WM] Payload length: {len(payload)} chars → {len(bits)} bits")

    # Open video
    cap = cv2.VideoCapture(str(input_file))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    log.append(f"[WM] Video: {width}x{height} @ {fps:.1f}fps, {total_frames} frames")

    # Video writer (MP4V codec → .mp4)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    frame_idx = 0
    max_frames = MAX_WATERMARK_FRAMES if MAX_WATERMARK_FRAMES > 0 else total_frames

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx < max_frames:
            # Convert BGR → YCrCb
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            y_channel = ycrcb[:, :, 0]

            # Embed watermark in Y channel
            y_wm = _embed_watermark_frame(y_channel, bits, WATERMARK_STRENGTH)
            ycrcb[:, :, 0] = y_wm

            # Convert back
            frame = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()

    log.append(f"[WM] Watermarked {min(frame_idx, max_frames)} / {frame_idx} frames")

    # Re-mux with FFmpeg to ensure wide compatibility & copy audio back in
    final_output = wm_folder / f"watermarked_{input_file.stem}.mp4"
    mux_cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(output_path),     # watermarked video (no audio)
        "-i", str(input_file),      # original (has audio)
        "-c:v", "copy",
        "-c:a", "aac",              # re-encode audio to AAC
        "-map", "0:v:0",            # video from watermarked
        "-map", "1:a:0?",           # audio from original (optional)
        "-shortest",
        str(final_output),
    ]
    try:
        run_cmd(mux_cmd, timeout=300)
        # Remove intermediate file
        output_path.unlink(missing_ok=True)
        output_path = final_output
        log.append("[WM] Audio re-muxed successfully")
    except Exception as e:
        log.append(f"[WM] Audio mux skipped (no audio track or error): {e}")
        # Keep the video-only watermarked file
        if not output_path.exists() and final_output.exists():
            output_path = final_output

    # Write sidecar metadata (needed for watermark extraction later)
    sidecar = {
        "watermark_id": watermark_id,
        "content_id": content_id,
        "owner_id": owner_id,
        "user_id": user_id,
        "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
        "bit_count": len(bits),
        "strength": WATERMARK_STRENGTH,
        "wavelet": WAVELET,
        "embedded_at": now_iso(),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    log.append(f"[WM] Sidecar written to {sidecar_path}")
    log.append(f"[WM] Finished at {now_iso()}")

    return {
        "watermarked_media_path": str(output_path),
        "watermark_id": watermark_id,
        "sidecar_path": str(sidecar_path),
        "processing_log": "\n".join(log),
    }


def embed_watermark_audio(
    input_path: str,
    content_id: str,
    watermark_text: str,
    owner_id: str = "",
    user_id: str = "",
) -> dict:
    """
    Embed an invisible DWT watermark into an audio file.
    Uses PyWavelets on the raw waveform loaded via librosa.
    """
    import librosa
    import soundfile as sf

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input media not found: {input_path}")

    log: list[str] = [f"[WM-Audio] Started at {now_iso()}"]

    wm_folder = OUTPUT_DIR / content_id / "watermarked"
    wm_folder.mkdir(parents=True, exist_ok=True)
    output_path = wm_folder / f"watermarked_{input_file.stem}.wav"
    sidecar_path = wm_folder / "watermark_sidecar.json"

    if user_id:
        payload = f"{watermark_text}|uid:{user_id}"
    else:
        payload = watermark_text
    watermark_id = hashlib.sha256(payload.encode()).hexdigest()[:16]
    bits = _text_to_bits(payload)

    # Load audio
    y, sr = librosa.load(str(input_file), sr=None, mono=True)
    log.append(f"[WM-Audio] Loaded {len(y)} samples @ {sr} Hz")

    # DWT on the entire waveform
    coeffs = pywt.wavedec(y, WAVELET, level=4)
    approx = coeffs[0]

    # Embed bits cyclically into approximation coefficients
    strength = WATERMARK_STRENGTH * 0.01  # gentler for audio
    for i, bit in enumerate(bits):
        idx = i % len(approx)
        if bit == 1:
            approx[idx] += strength * abs(approx[idx])
        else:
            approx[idx] -= strength * abs(approx[idx])
    coeffs[0] = approx

    # Reconstruct
    y_wm = pywt.waverec(coeffs, WAVELET)
    y_wm = y_wm[:len(y)]  # trim to original length

    # Save
    sf.write(str(output_path), y_wm, sr)
    log.append(f"[WM-Audio] Written to {output_path}")

    sidecar = {
        "watermark_id": watermark_id,
        "content_id": content_id,
        "owner_id": owner_id,
        "user_id": user_id,
        "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
        "bit_count": len(bits),
        "strength": strength,
        "wavelet": WAVELET,
        "embedded_at": now_iso(),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    log.append(f"[WM-Audio] Finished at {now_iso()}")

    return {
        "watermarked_media_path": str(output_path),
        "watermark_id": watermark_id,
        "sidecar_path": str(sidecar_path),
        "processing_log": "\n".join(log),
    }


def embed_watermark(
    input_path: str,
    content_id: str,
    watermark_text: str,
    owner_id: str = "",
    user_id: str = "",
) -> dict:
    """
    Dispatcher: automatically picks video or audio watermarking
    based on file extension.
    """
    if is_video(input_path):
        return embed_watermark_video(input_path, content_id, watermark_text, owner_id, user_id)
    elif is_audio(input_path):
        return embed_watermark_audio(input_path, content_id, watermark_text, owner_id, user_id)
    else:
        raise ValueError(f"Unsupported media type for watermarking: {input_path}")
