import os

import cv2
import imagehash
import yt_dlp
from PIL import Image
from yt_dlp.utils import download_range_func


def extract_hashes(video_path, max_frames=20):
    hashes = []
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    while cap.isOpened() and len(hashes) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 30 == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            phash = imagehash.phash(pil_img)
            hashes.append(str(phash))

        frame_count += 1

    cap.release()
    return hashes


def download_and_extract(url: str) -> tuple[str, list[str]]:
    video_path = None
    try:
        os.makedirs("data/temp", exist_ok=True)

        with yt_dlp.YoutubeDL({"quiet": True}) as info_ydl:
            info = info_ydl.extract_info(url, download=False)
            video_id = info.get("id", "temp_video")

        video_path = os.path.join("data", "temp", f"{video_id}.mp4")
        ydl_opts = {
            "format": "worst",
            "outtmpl": video_path,
            "quiet": True,
            "download_ranges": download_range_func(None, [(0, 30)]),
            "force_keyframes_at_cuts": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        hashes = extract_hashes(video_path)

        if video_path and os.path.exists(video_path):
            os.remove(video_path)

        return video_path, hashes
    except Exception:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        return None, []
