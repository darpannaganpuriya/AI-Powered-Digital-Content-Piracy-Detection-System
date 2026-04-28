from crawler import crawl_all
from fingerprint import extract_hashes
from matcher import compute_similarity
from ai_engine import detect_piracy
from config import SIMILARITY_THRESHOLD

import yt_dlp
import time


#  Initial input (Sakshi + Aditya output simulation)
input_data = {
    "content_id": "123",
    "fingerprint_hash": None,   # 🔥 IMPORTANT: start with None
    "metadata": {
        "title": "IPL Highlights",
        "keywords": ["IPL", "cricket"]
    },
    "ownership_verified": True
}


#  Download video
def download_video(url):
    ydl_opts = {
        'format': 'worst',
        'outtmpl': 'temp/%(id)s.%(ext)s',
        'quiet': True,
        'download_sections': ['*0-30'],   # 🔥 only first 30 seconds
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


#  Main pipeline
def run_pipeline():
    crawled_data = crawl_all(input_data["metadata"])

    for item in crawled_data:
        try:
            print("\n🔍 Processing:", item["url"])

            path = download_video(item["url"])

            hashes = extract_hashes(path)

            print("📊 Hashes extracted:", len(hashes))

            # 🔥 IMPORTANT: First video → use as reference fingerprint
            if input_data["fingerprint_hash"] is None:
                 if len(hashes) > 0:
                    input_data["fingerprint_hash"] = hashes[0]
                    print("✅ Reference fingerprint set")
                 else:
                  print("⚠️ No hashes found, skipping")
                  continue
            #  Compute similarity
            sim = compute_similarity(
                input_data["fingerprint_hash"],
                hashes
            )

            print("📊 Similarity:", sim)
            print("📊 Sample Hash:", hashes[0])
            print("📊 Reference Hash:", input_data["fingerprint_hash"])
            

            #  Detection
            if sim > SIMILARITY_THRESHOLD:
                verdict, conf = detect_piracy(
                    item["title"],
                    sim,
                    input_data["ownership_verified"]
                )

                print("\n🚨 DETECTED")
                print("URL:", item["url"])
                print("Platform:", item["platform"])
                print("Similarity:", sim)
                print("Verdict:", verdict)
                print("Confidence:", conf)

        except Exception as e:
         msg = str(e).lower()

         if "bot" in msg or "sign in" in msg:
          print("⚠️ Bot blocked — skipping")
         elif "unavailable" in msg:
          print("⚠️ Video unavailable")
         else:
          print("❌ Error:", e)

          continue

         time.sleep(2)
         
         print("📊 Total crawled videos:", len(crawled_data))
         
#  Run once (no scheduler for now)
if __name__ == "__main__":
    run_pipeline()