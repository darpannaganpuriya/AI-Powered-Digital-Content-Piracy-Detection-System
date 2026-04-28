"""
DRM / Encryption Module
========================
Encrypts media into AES-128 encrypted HLS segments using FFmpeg.

How it works:
1. Generate a random 16-byte AES key and a unique Key-ID.
2. Write the raw key to a file that the HLS player would fetch from a license server.
3. Create a key-info file that tells FFmpeg where the key lives.
4. Run FFmpeg to segment the input into .ts chunks encrypted with AES-128-CBC,
   producing an HLS manifest (.m3u8).
5. Return paths + DRM metadata so downstream modules and the API can use them.

This is *real* AES-128 HLS encryption — the same mechanism used by production
CDNs (Akamai, CloudFront) for clear-key DRM.
"""

import os
import shutil
from pathlib import Path

from config import (
    FFMPEG_BIN,
    AES_KEY_LENGTH,
    HLS_SEGMENT_DURATION,
    OUTPUT_DIR,
)
from utils.helpers import generate_hex_key, generate_key_id, run_cmd, now_iso


def _write_key_files(output_folder: Path, hex_key: str, key_id: str):
    """
    Create the two files FFmpeg needs for AES-128 HLS encryption:
    - encryption.key  : the raw 16-byte key
    - encryption.keyinfo : pointer file (key URI, key file path, IV)
    """
    key_file = output_folder / "encryption.key"
    keyinfo_file = output_folder / "encryption.keyinfo"

    # Write raw binary key
    key_bytes = bytes.fromhex(hex_key)
    key_file.write_bytes(key_bytes)

    # The key-info file has 3 lines:
    #   1) URI the player will use to fetch the key (simulate a license server)
    #   2) Local path to the key file (used by FFmpeg during packaging)
    #   3) IV in hex (we reuse the key_id padded to 32 hex chars)
    iv = key_id[:32].ljust(32, "0")
    keyinfo_content = f"encryption.key\n{key_file}\n{iv}\n"
    keyinfo_file.write_text(keyinfo_content)

    return key_file, keyinfo_file, iv


def encrypt_media(
    input_path: str,
    content_id: str,
    owner_id: str = "",
) -> dict:
    """
    Encrypt a media file into AES-128 HLS segments.

    Parameters
    ----------
    input_path : str
        Absolute path to the source media file (video or audio).
    content_id : str
        Unique identifier for this content.
    owner_id : str, optional
        Owner identifier stored in metadata.

    Returns
    -------
    dict with keys:
        encrypted_media_path : str   – folder containing encrypted segments + manifest
        manifest_path        : str   – path to the .m3u8 playlist
        drm_key_hex          : str   – hex representation of the AES key
        drm_key_id           : str   – unique key identifier
        drm_iv               : str   – initialisation vector (hex)
        drm_license_info     : dict  – simulated license-server metadata
        processing_log       : str   – human-readable log of steps taken
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input media not found: {input_path}")

    log_lines: list[str] = []
    log_lines.append(f"[DRM] Started at {now_iso()}")

    # --- 1. Prepare output folder -------------------------------------------
    drm_folder = OUTPUT_DIR / content_id / "drm"
    drm_folder.mkdir(parents=True, exist_ok=True)
    log_lines.append(f"[DRM] Output folder: {drm_folder}")

    # --- 2. Generate encryption material ------------------------------------
    hex_key = generate_hex_key(AES_KEY_LENGTH)
    key_id = generate_key_id()
    key_file, keyinfo_file, iv = _write_key_files(drm_folder, hex_key, key_id)
    log_lines.append(f"[DRM] Generated AES-128 key  (key_id={key_id[:8]}…)")

    # --- 3. Build FFmpeg command --------------------------------------------
    manifest_path = drm_folder / "manifest.m3u8"
    segment_pattern = str(drm_folder / "segment_%03d.ts")

    cmd = [
        FFMPEG_BIN,
        "-y",                           # overwrite existing files
        "-i", str(input_file),          # input
        "-c", "copy",                   # no re-encoding (fast)
        "-hls_time", str(HLS_SEGMENT_DURATION),
        "-hls_list_size", "0",          # keep all segments in manifest
        "-hls_key_info_file", str(keyinfo_file),
        "-hls_segment_filename", segment_pattern,
        str(manifest_path),
    ]
    log_lines.append(f"[DRM] FFmpeg command: {' '.join(cmd)}")

    # --- 4. Run FFmpeg -------------------------------------------------------
    try:
        result = run_cmd(cmd, timeout=300)
        log_lines.append("[DRM] FFmpeg completed successfully")
        if result.stderr:
            # FFmpeg writes progress to stderr – keep last 500 chars
            log_lines.append(f"[DRM] FFmpeg stderr (tail): …{result.stderr[-500:]}")
    except Exception as e:
        log_lines.append(f"[DRM] FFmpeg FAILED: {e}")
        raise RuntimeError(f"DRM encryption failed: {e}") from e

    # --- 5. Build simulated license-server info ------------------------------
    drm_license_info = {
        "license_server_url": f"http://localhost:8000/drm/keys/{content_id}",
        "key_id": key_id,
        "encryption_scheme": "AES-128-CBC",
        "key_delivery": "clear-key (simulated)",
        "note": (
            "In production, replace this with a Widevine/FairPlay/PlayReady "
            "license server endpoint. The AES key would be delivered via "
            "a secure key-exchange protocol, not stored on disk."
        ),
    }

    log_lines.append(f"[DRM] Finished at {now_iso()}")

    return {
        "encrypted_media_path": str(drm_folder),
        "manifest_path": str(manifest_path),
        "drm_key_hex": hex_key,
        "drm_key_id": key_id,
        "drm_iv": iv,
        "drm_license_info": drm_license_info,
        "processing_log": "\n".join(log_lines),
    }
