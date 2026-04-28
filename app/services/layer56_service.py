from datetime import datetime
import asyncio
from typing import List

import httpx

from app.services.ai_enrichment import enrich_scraped_items_async
from app.services.ai_engine_service import SIMILARITY_THRESHOLD, detect_piracy
from app.services.crawler_service import crawl_for_content
from app.services.fingerprint_service import download_and_extract
from app.services.matcher_service import match_against_reference


DECISION_API_URL = "http://127.0.0.1:8000/api/v1/decision/process"


def decode_leak_source(watermark_id: str) -> str:
    watermark = (watermark_id or "").lower()
    if "broadcaster" in watermark:
        return "broadcaster"
    if "user_" in watermark:
        return "user"
    if "platform_" in watermark:
        return "platform"
    return "unknown"


def run_detection(
    content_id,
    fingerprint_hash,
    watermark_id,
    owner_id,
    blockchain_tx_hash,
    metadata,
    ownership_verified=True,
) -> List[dict]:
    results = []
    ai_context_items = []
    crawled_urls = crawl_for_content(metadata)
    run_detection.last_total_crawled = len(crawled_urls)

    for item in crawled_urls:
        _, hashes = download_and_extract(item["url"])
        if not hashes:
            continue

        similarity = match_against_reference(fingerprint_hash, hashes)
        if similarity > SIMILARITY_THRESHOLD:
            verdict, confidence = detect_piracy(
                item["title"], similarity, ownership_verified
            )
            if verdict in ["PIRACY", "SUSPICIOUS"]:
                # Compute risk
                if similarity > 0.9:
                    risk = "HIGH"
                elif similarity > 0.7:
                    risk = "MEDIUM"
                else:
                    risk = "LOW"

                # Compute action
                if risk == "HIGH":
                    action = "TAKEDOWN"
                elif risk == "MEDIUM":
                    action = "MONITOR"
                else:
                    action = "IGNORE"

                result = {
                    "url": item["url"],
                    "platform": item["platform"],
                    "similarity": similarity,
                    "verdict": verdict,
                    "confidence": confidence,
                    "risk": risk,
                    "action": action,
                    "sample_hash": hashes[0] if hashes else "",
                    "reference_hash": fingerprint_hash,
                    "detected_at": datetime.utcnow().isoformat(),
                    "content_id": content_id,
                    "watermark_id": watermark_id,
                    "owner_id": owner_id,
                    "blockchain_tx_hash": blockchain_tx_hash,
                    "leak_source": decode_leak_source(watermark_id),
                    "action_required": "TAKEDOWN"
                    if confidence >= 0.9
                    else "REVENUE_REDIRECT",
                    "ownership_verified": ownership_verified,
                }
                results.append(result)
                ai_context_items.append(
                    {
                        "source_url": item.get("url"),
                        "media_sample_path": None,
                        "platform": item.get("platform"),
                        "timestamp": result.get("detected_at"),
                    }
                )

    if results:
        try:
            ai_results = asyncio.run(enrich_scraped_items_async(ai_context_items))
        except Exception:
            ai_results = [None for _ in results]

        for idx, result in enumerate(results):
            result["ai_analysis"] = ai_results[idx] if idx < len(ai_results) else None

    for result in results:
        if result.get("verdict") in ["PIRACY", "SUSPICIOUS"]:
            try:
                httpx.post(DECISION_API_URL, json=result, timeout=10)
            except Exception:
                pass

    return results
