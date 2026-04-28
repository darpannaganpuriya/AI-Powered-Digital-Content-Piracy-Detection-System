"""
Utility helpers for the Content Protection System.
"""

import hashlib
import secrets
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone


def generate_hex_key(length: int = 16) -> str:
    """Generate a cryptographically secure random hex key."""
    return secrets.token_hex(length)


def generate_key_id() -> str:
    """Generate a unique key-id (UUID-style hex)."""
    return secrets.token_hex(16)


def sha256_file(filepath: str | Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def run_cmd(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    """
    Run a subprocess command and return the result.
    Raises subprocess.CalledProcessError on non-zero exit.
    """
    return subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def probe_media(filepath: str, ffprobe_bin: str = "ffprobe") -> dict:
    """
    Use ffprobe to extract media metadata (duration, codec, resolution, etc.).
    Returns parsed JSON from ffprobe.
    """
    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(filepath),
    ]
    result = run_cmd(cmd)
    return json.loads(result.stdout)


def is_video(filepath: str) -> bool:
    """Check if a file is a video based on extension."""
    return Path(filepath).suffix.lower() in {".mp4", ".mkv", ".avi", ".mov", ".webm"}


def is_audio(filepath: str) -> bool:
    """Check if a file is an audio file based on extension."""
    return Path(filepath).suffix.lower() in {".mp3", ".wav", ".flac", ".aac", ".ogg"}
