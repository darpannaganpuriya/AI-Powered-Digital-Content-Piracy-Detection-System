import cv2
from PIL import Image
import imagehash

def extract_hashes(video_path, max_frames=20):
    cap = cv2.VideoCapture(video_path)
    hashes = []
    count = 0

    while len(hashes) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if count % 30 == 0:   # skip frames → faster
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            hashes.append(str(imagehash.phash(img)))

        count += 1

    cap.release()
    return hashes