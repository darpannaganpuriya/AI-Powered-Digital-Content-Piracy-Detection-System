#!/usr/bin/env python3
"""
Pipeline Demo — Offline End-to-End Test
========================================

Runs the ENTIRE piracy detection pipeline by calling all layer modules
directly — NO servers required.

This is the quickest way to verify that all layers connect and data flows
end-to-end.

Flow:
  1. Layer 1-2: Simulate content protection (DRM + Watermark + Fingerprint)
  2. Layer 3-4: Blockchain ownership + Feature vector generation
  3. Layer 5-6: Internet crawling → Download → Fingerprint extraction → Matching
  4. Layer 7:   Detection verdict → Risk prediction → Decision → Alert

Usage:
    python pipeline_demo.py
    python pipeline_demo.py --keywords "IPL highlights" "cricket match"
    python pipeline_demo.py --file Layer1-2/test_sample.mp4
    python pipeline_demo.py --skip-crawl   (skip internet crawling, use mock data)

This script imports from all layers directly and wires them together.
"""

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
#  Setup sys.path so all modules are importable
# ──────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Ensure data directories exist
os.makedirs("data/temp", exist_ok=True)
os.makedirs("data", exist_ok=True)


# ──────────────────────────────────────────────────────────────────────
#  Import Layer modules
# ──────────────────────────────────────────────────────────────────────

# Layer 3-4 services (direct import — NOT via HTTP)
from app.services.blockchain_service import BlockchainService
from app.services.feature_service import FeatureService

# Layer 5-6 services (direct import)
from app.services.crawler_service import crawl_for_content
from app.services.fingerprint_service import download_and_extract
from app.services.matcher_service import match_against_reference
from app.services.ai_engine_service import SIMILARITY_THRESHOLD, detect_piracy


# ──────────────────────────────────────────────────────────────────────
#  Layer 1-2: Content Protection (Simulate or Use Real Modules)
# ──────────────────────────────────────────────────────────────────────

def run_layer12(file_path: str | None, content_id: str, owner_id: str) -> dict:
    """
    Run Layer 1-2: DRM + Watermark + Fingerprint.
    
    If a real media file is provided, tries to use actual Layer 1-2 modules.
    Otherwise, generates a simulated protection output.
    """
    print("\n" + "═" * 60)
    print("  LAYER 1-2: Content Protection (DRM + Watermark + Fingerprint)")
    print("═" * 60)

    fingerprint_hash = ""
    watermark_id = f"CPS:{content_id}:{owner_id}"

    # Try to use real Layer 1-2 fingerprint module
    if file_path and Path(file_path).exists():
        try:
            # Temporarily add Layer1-2 backend to path for its modules
            layer12_path = str(BASE_DIR / "Layer1-2" / "backend")
            if layer12_path not in sys.path:
                sys.path.insert(0, layer12_path)
            from modules.fingerprint import generate_fingerprint
            fp_result = generate_fingerprint(file_path, content_id)
            fingerprint_hash = fp_result.get("fingerprint_hash", "")
            print(f"  ✅ Real fingerprint generated: {fingerprint_hash[:20]}...")
        except Exception as e:
            print(f"  ⚠️ Real fingerprint failed ({e}), using simulated hash")

    # Fallback: generate simulated fingerprint hash
    if not fingerprint_hash:
        seed = f"{content_id}|{owner_id}|{datetime.now().isoformat()}"
        fingerprint_hash = hashlib.sha256(seed.encode()).hexdigest()
        print(f"  📝 Simulated fingerprint hash: {fingerprint_hash[:20]}...")

    result = {
        "content_id": content_id,
        "encrypted_media_path": f"outputs/{content_id}/encrypted/master.m3u8",
        "drm_license_info": json.dumps({
            "type": "AES-128-HLS",
            "key_id": content_id,
            "issued_to": owner_id,
        }),
        "watermark_id": watermark_id,
        "fingerprint_hash": fingerprint_hash,
        "metadata": {
            "owner_id": owner_id,
            "title": "Sports Media Content",
            "keywords": ["IPL", "cricket", "highlights"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    print(f"  Content ID:       {result['content_id']}")
    print(f"  Watermark ID:     {result['watermark_id']}")
    print(f"  Fingerprint:      {result['fingerprint_hash'][:20]}...")
    print(f"  DRM Encrypted:    Yes")
    print("  ✅ Layer 1-2 complete\n")

    return result


# ──────────────────────────────────────────────────────────────────────
#  Layer 3-4: Ownership + Intelligence
# ──────────────────────────────────────────────────────────────────────

def run_layer34(layer12_output: dict) -> dict:
    """
    Run Layer 3-4: Blockchain ownership registration + Feature vector.
    Uses the ACTUAL blockchain and feature services (no HTTP).
    """
    print("═" * 60)
    print("  LAYER 3-4: Ownership + Intelligence (Blockchain + Features)")
    print("═" * 60)

    content_id = layer12_output["content_id"]
    fingerprint_hash = layer12_output["fingerprint_hash"]
    watermark_id = layer12_output["watermark_id"]
    metadata = layer12_output.get("metadata", {})

    # Use actual service classes
    blockchain_svc = BlockchainService(
        network="polygon_mumbai",
        tx_prefix="0x",
        secret_salt="sports_media_protection_salt",
    )
    feature_svc = FeatureService(vector_size=16)

    # Register ownership on blockchain
    blockchain_tx_hash, ownership_verified = blockchain_svc.register_ownership(
        content_id=content_id,
        fingerprint_hash=fingerprint_hash,
        watermark_id=watermark_id,
    )

    # Generate feature vector
    feature_vector = feature_svc.create_feature_vector(
        content_id=content_id,
        fingerprint_hash=fingerprint_hash,
        metadata=metadata,
    )

    result = {
        "content_id": content_id,
        "fingerprint_hash": fingerprint_hash,
        "watermark_id": watermark_id,
        "feature_vector": feature_vector,
        "blockchain_tx_hash": blockchain_tx_hash,
        "blockchain_network": "polygon_mumbai",
        "ownership_verified": ownership_verified,
        "ai_model_version": "v1.0",
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }

    print(f"  Blockchain TX:    {blockchain_tx_hash[:20]}...")
    print(f"  Ownership:        {'✅ Verified' if ownership_verified else '❌ Not Verified'}")
    print(f"  Feature Vector:   [{len(feature_vector)} dimensions]")
    print(f"  Network:          polygon_mumbai")
    print("  ✅ Layer 3-4 complete\n")

    return result


# ──────────────────────────────────────────────────────────────────────
#  Layer 5-6-7: Detection Pipeline
# ──────────────────────────────────────────────────────────────────────

def run_layer567(
    layer12_output: dict,
    layer34_output: dict,
    skip_crawl: bool = False,
    custom_keywords: list[str] | None = None,
) -> list[dict]:
    """
    Run Layer 5-6-7: Crawling → Downloading → Fingerprinting → Matching → Detection.
    Uses actual service modules (no HTTP).
    """
    print("═" * 60)
    print("  LAYER 5-6-7: Detection Pipeline")
    print("  (Crawl → Download → Fingerprint → Match → Detect → Decide)")
    print("═" * 60)

    content_id = layer12_output["content_id"]
    fingerprint_hash = layer12_output["fingerprint_hash"]
    watermark_id = layer12_output["watermark_id"]
    metadata = layer12_output.get("metadata", {})
    owner_id = metadata.get("owner_id", "unknown")
    ownership_verified = layer34_output.get("ownership_verified", True)
    blockchain_tx_hash = layer34_output.get("blockchain_tx_hash", "")

    # Override keywords if provided
    if custom_keywords:
        metadata = dict(metadata)
        metadata["keywords"] = custom_keywords

    results = []

    # ── Crawl ────────────────────────────────────────────────────────
    if skip_crawl:
        print("  ⏭️  Skipping internet crawl (--skip-crawl)")
        crawled_urls = [
            {
                "url": "https://youtube.com/watch?v=MOCK_1",
                "title": "IPL Highlights Full Match Free",
                "platform": "youtube",
            },
            {
                "url": "https://youtube.com/watch?v=MOCK_2",
                "title": "Cricket Best Moments",
                "platform": "youtube",
            },
        ]
    else:
        print(f"  🌐 Crawling internet for: {metadata.get('keywords', [])}")
        try:
            crawled_urls = crawl_for_content(metadata)
            print(f"  📥 Found {len(crawled_urls)} URLs to scan")
        except Exception as e:
            print(f"  ⚠️ Crawling failed: {e}")
            crawled_urls = []

    if not crawled_urls:
        print("  ℹ️  No URLs found to scan")
        return results

    # ── Process each URL ─────────────────────────────────────────────
    for idx, item in enumerate(crawled_urls, 1):
        url = item.get("url", "")
        title = item.get("title", "")
        platform = item.get("platform", "unknown")

        print(f"\n  ── Scanning [{idx}/{len(crawled_urls)}]: {title[:50]}")
        print(f"     URL: {url}")

        try:
            # Download & extract fingerprint
            if skip_crawl:
                # Mock hashes for skip-crawl mode
                print("     📝 Using simulated hashes (skip-crawl mode)")
                hashes = [fingerprint_hash[:16]]  # partial match for demo
            else:
                print("     📥 Downloading (first 30s)...")
                _, hashes = download_and_extract(url)

            if not hashes:
                print("     ⚠️ No hashes extracted — skipping")
                continue

            print(f"     📊 Extracted {len(hashes)} hash(es)")

            # Compute similarity
            similarity = match_against_reference(fingerprint_hash, hashes)
            print(f"     📊 Similarity: {similarity:.4f}")

            # Detection verdict
            if similarity > SIMILARITY_THRESHOLD:
                verdict, confidence = detect_piracy(title, similarity, ownership_verified)
            else:
                verdict, confidence = "SAFE", 0.5

            # Risk level
            if similarity > 0.9:
                risk = "HIGH"
            elif similarity > 0.7:
                risk = "MEDIUM"
            else:
                risk = "LOW"

            # Action
            if risk == "HIGH" and verdict == "PIRACY":
                action = "TAKEDOWN"
            elif risk == "MEDIUM":
                action = "MONITOR"
            else:
                action = "IGNORE"

            # Leak source from watermark
            wm_lower = (watermark_id or "").lower()
            if "broadcaster" in wm_lower:
                leak_source = "broadcaster"
            elif "user_" in wm_lower:
                leak_source = "user"
            elif "platform_" in wm_lower:
                leak_source = "platform"
            else:
                leak_source = "unknown"

            result = {
                "url": url,
                "platform": platform,
                "similarity": round(similarity, 4),
                "verdict": verdict,
                "confidence": confidence,
                "risk": risk,
                "action": action,
                "watermark_id": watermark_id,
                "ownership_verified": ownership_verified,
                "content_id": content_id,
                "blockchain_tx_hash": blockchain_tx_hash,
                "leak_source": leak_source,
                "detected_at": datetime.utcnow().isoformat(),
                "sample_hash": hashes[0] if hashes else "",
                "reference_hash": fingerprint_hash,
            }

            results.append(result)

            # Print detection
            if verdict in ["PIRACY", "SUSPICIOUS"]:
                emoji = "🚨" if verdict == "PIRACY" else "⚠️"
                print(f"     {emoji} {verdict} (confidence: {confidence})")
                print(f"        Risk: {risk} | Action: {action}")
            else:
                print(f"     ✅ {verdict}")

        except Exception as e:
            msg = str(e).lower()
            if "bot" in msg or "sign in" in msg:
                print("     ⚠️ Bot detection — skipping")
            elif "unavailable" in msg:
                print("     ⚠️ Video unavailable — skipping")
            else:
                print(f"     ❌ Error: {e}")
            continue

        time.sleep(1)  # rate limiting

    print(f"\n  📊 Scanned {len(crawled_urls)} URLs, found {len(results)} matches")
    print("  ✅ Layer 5-6-7 complete\n")

    return results


# ──────────────────────────────────────────────────────────────────────
#  Final Output Formatter
# ──────────────────────────────────────────────────────────────────────

def format_final_output(
    layer12: dict,
    layer34: dict,
    detections: list[dict],
) -> dict:
    """Build the full pipeline output with all layers' data."""
    content_id = layer12.get("content_id", "unknown")

    piracy_count = sum(1 for d in detections if d.get("verdict") == "PIRACY")
    suspicious_count = sum(1 for d in detections if d.get("verdict") == "SUSPICIOUS")
    safe_count = sum(1 for d in detections if d.get("verdict") == "SAFE")

    return {
        "pipeline_run": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_id": content_id,
            "status": "COMPLETE",
        },
        "content_protection": {
            "content_id": content_id,
            "fingerprint_hash": layer12.get("fingerprint_hash", ""),
            "watermark_id": layer12.get("watermark_id", ""),
            "drm_applied": bool(layer12.get("encrypted_media_path")),
        },
        "ownership": {
            "blockchain_tx_hash": layer34.get("blockchain_tx_hash", ""),
            "blockchain_network": layer34.get("blockchain_network", ""),
            "ownership_verified": layer34.get("ownership_verified", False),
            "feature_vector_dimensions": len(layer34.get("feature_vector", [])),
        },
        "detection_summary": {
            "total_scanned": len(detections),
            "piracy": piracy_count,
            "suspicious": suspicious_count,
            "safe": safe_count,
        },
        "detections": [
            {
                "url": d.get("url", ""),
                "similarity": d.get("similarity", 0.0),
                "verdict": d.get("verdict", "SAFE"),
                "risk": d.get("risk", "LOW"),
                "action": d.get("action", "IGNORE"),
                "watermark_id": d.get("watermark_id", ""),
                "ownership_verified": d.get("ownership_verified", False),
            }
            for d in detections
        ],
    }


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Offline End-to-End Pipeline Demo — No servers required",
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to a media file for real fingerprinting",
        default=None,
    )
    parser.add_argument(
        "--content-id",
        help="Content ID (auto-generated if not provided)",
        default=None,
    )
    parser.add_argument(
        "--owner-id",
        help="Owner ID",
        default="owner_default",
    )
    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        help="Custom search keywords for crawling",
        default=None,
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip internet crawling (use mock data for demo)",
    )
    args = parser.parse_args()

    content_id = args.content_id or f"cid_{uuid.uuid4().hex[:12]}"

    print("\n" + "█" * 60)
    print("  🛡️  AI Digital Content Piracy Detection System")
    print("  Offline Pipeline Demo (Direct Module Invocation)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("█" * 60)

    start_time = time.time()

    try:
        # ── Layer 1-2 ────────────────────────────────────────────────
        layer12_result = run_layer12(
            file_path=args.file,
            content_id=content_id,
            owner_id=args.owner_id,
        )

        # ── Layer 3-4 ────────────────────────────────────────────────
        layer34_result = run_layer34(layer12_result)

        # ── Layer 5-6-7 ─────────────────────────────────────────────
        detections = run_layer567(
            layer12_output=layer12_result,
            layer34_output=layer34_result,
            skip_crawl=args.skip_crawl,
            custom_keywords=args.keywords,
        )

        # ── Final Output ─────────────────────────────────────────────
        final = format_final_output(layer12_result, layer34_result, detections)

        elapsed = time.time() - start_time

        print("═" * 60)
        print("  FINAL PIPELINE OUTPUT")
        print("═" * 60)
        print(json.dumps(final, indent=2))

        # Save to file
        output_path = Path(f"pipeline_output_{content_id}.json")
        output_path.write_text(json.dumps(final, indent=2))

        # Summary
        summary = final["detection_summary"]
        print("\n" + "═" * 60)
        print("  PIPELINE SUMMARY")
        print("═" * 60)
        print(f"  Content ID:        {content_id}")
        print(f"  Owner ID:          {args.owner_id}")
        print(f"  Ownership:         {'✅ Verified' if final['ownership'].get('ownership_verified') else '❌ Not Verified'}")
        print(f"  URLs Scanned:      {summary['total_scanned']}")
        print(f"  🔴 PIRACY:         {summary['piracy']}")
        print(f"  🟡 SUSPICIOUS:     {summary['suspicious']}")
        print(f"  🟢 SAFE:           {summary['safe']}")
        print(f"  Time Elapsed:      {elapsed:.1f}s")
        print(f"  Output Saved:      {output_path}")
        print("═" * 60)
        print("  ✅ Pipeline execution complete!")
        print("═" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\n⛔ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
