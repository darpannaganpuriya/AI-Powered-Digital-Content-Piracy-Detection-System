#!/usr/bin/env python3
"""
Integrated Pipeline Controller
===============================

End-to-end orchestrator for the Digital Content Piracy Detection System.

Flow:
  Input Media File
       ↓
  Layer 1-2  ─ DRM encryption + Watermark embedding + Fingerprint generation
       ↓
  Layer 3-4  ─ Blockchain ownership registration + Feature vector creation
       ↓
  Layer 5-6  ─ Internet crawling + Download + Fingerprint extraction + Matching
       ↓
  Layer 7    ─ Detection verdicts + Risk prediction + Decision + Alerts
       ↓
  Final Structured Output

Usage:
    python integrated_pipeline.py <media_file_path> [content_id] [owner_id]

Requirements:
    Both services must be running:
      python run_all.py
    Or start manually:
      Layer 1-2: uvicorn app:app --port 8001  (from Layer1-2/backend/)
      Layer 3-7: uvicorn app.main:app --port 8000  (from project root)
"""

import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


# ──────────────────────────────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────────────────────────────

LAYER12_URL = "http://127.0.0.1:8001"
MAIN_APP_URL = "http://127.0.0.1:8000"

POLL_INTERVAL = 5    # seconds between status checks
MAX_POLL_WAIT = 120  # max seconds to wait for async processing


# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────

def _check_service(name: str, base_url: str) -> bool:
    """Check if a service is reachable."""
    try:
        resp = httpx.get(f"{base_url}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _print_header(msg: str):
    print(f"\n{'─' * 60}")
    print(f"  {msg}")
    print(f"{'─' * 60}")


def _print_json(data: dict):
    print(json.dumps(data, indent=2, default=str))


# ──────────────────────────────────────────────────────────────────────
#  Step 1: Upload to Layer 1-2
# ──────────────────────────────────────────────────────────────────────

def step_layer12(file_path: str, content_id: str, owner_id: str) -> dict:
    """Upload media to Layer 1-2 for DRM + Watermark + Fingerprint."""
    _print_header("STEP 1 — Layer 1-2: Content Protection")

    url = f"{LAYER12_URL}/process"
    p = Path(file_path)

    with open(p, "rb") as f:
        files = {"file": (p.name, f, "video/mp4")}
        data = {
            "content_id": content_id or f"cid_{uuid.uuid4().hex[:12]}",
            "owner_id": owner_id,
        }

        print(f"📤 Uploading: {p.name}")
        resp = httpx.post(url, files=files, data=data, timeout=120)
        resp.raise_for_status()

    result = resp.json()
    print(f"✅ Layer 1-2 complete")
    print(f"   Content ID:        {result.get('content_id', 'N/A')}")
    fp_hash = result.get("fingerprint_hash", "")
    print(f"   Fingerprint Hash:  {fp_hash[:20]}..." if len(fp_hash) > 20 else f"   Fingerprint Hash:  {fp_hash}")
    print(f"   Watermark ID:      {result.get('watermark_id', 'N/A')}")
    print(f"   DRM Encrypted:     {'Yes' if result.get('encrypted_media_path') else 'No'}")

    return result


# ──────────────────────────────────────────────────────────────────────
#  Step 2: Poll Layer 3-4 for ownership registration
# ──────────────────────────────────────────────────────────────────────

def step_layer34(content_id: str) -> dict | None:
    """Poll Layer 3-4 until ownership is registered."""
    _print_header("STEP 2 — Layer 3-4: Ownership + Intelligence")

    url = f"{MAIN_APP_URL}/api/v1/layers/3-4/content/{content_id}"
    waited = 0

    while waited < MAX_POLL_WAIT:
        try:
            resp = httpx.get(url, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ Layer 3-4 complete")
                tx_hash = result.get("blockchain_tx_hash", "")
                print(f"   Blockchain TX:     {tx_hash[:20]}..." if len(tx_hash) > 20 else f"   Blockchain TX:     {tx_hash}")
                print(f"   Ownership:         {'✅ Verified' if result.get('ownership_verified') else '❌ Not Verified'}")
                fv = result.get("feature_vector", [])
                print(f"   Feature Vector:    [{len(fv)} dimensions]")
                print(f"   AI Model:          {result.get('ai_model_version', 'N/A')}")
                return result
            elif resp.status_code == 404:
                print(f"   ⏳ Waiting for ownership registration... ({waited}s)")
        except Exception as e:
            print(f"   ⚠️ Connection issue: {e}")

        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL

    print("   ⚠️ Layer 3-4 processing timed out — continuing pipeline")
    return None


# ──────────────────────────────────────────────────────────────────────
#  Step 3: Poll Layer 5-6 for detection results
# ──────────────────────────────────────────────────────────────────────

def step_layer56(content_id: str) -> dict | None:
    """Poll Layer 5-6 for scan results."""
    _print_header("STEP 3 — Layer 5-6-7: Detection + Matching + Decision")

    url = f"{MAIN_APP_URL}/api/v1/layer56/scan/{content_id}"
    waited = 0

    while waited < MAX_POLL_WAIT:
        try:
            resp = httpx.get(url, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                data = result.get("data", [])
                if data:
                    print(f"✅ Detection scan complete — {len(data)} detection(s) found")
                    return result
                else:
                    print(f"   ⏳ Scan in progress... ({waited}s)")
        except Exception as e:
            print(f"   ⚠️ Connection issue: {e}")

        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL

    print("   ⏳ No detections found within polling window (this is normal for new content)")
    return None


# ──────────────────────────────────────────────────────────────────────
#  Step 4: Retrieve dashboard summary
# ──────────────────────────────────────────────────────────────────────

def step_dashboard() -> dict | None:
    """Retrieve the dashboard summary."""
    try:
        resp = httpx.get(f"{MAIN_APP_URL}/api/v1/dashboard/summary", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", {})
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────
#  Build Final Output
# ──────────────────────────────────────────────────────────────────────

def build_final_output(
    layer12: dict,
    layer34: dict | None,
    layer56: dict | None,
) -> list[dict]:
    """Build the final structured output combining all layer results."""
    content_id = layer12.get("content_id", "unknown")
    watermark_id = layer12.get("watermark_id", "")
    fingerprint_hash = layer12.get("fingerprint_hash", "")

    ownership_verified = False
    blockchain_tx_hash = ""
    feature_vector = []

    if layer34:
        ownership_verified = layer34.get("ownership_verified", False)
        blockchain_tx_hash = layer34.get("blockchain_tx_hash", "")
        feature_vector = layer34.get("feature_vector", [])

    detections = []
    if layer56 and layer56.get("data"):
        for det in layer56["data"]:
            detections.append({
                "content_id": content_id,
                "url": det.get("url", ""),
                "platform": det.get("platform", ""),
                "similarity": det.get("similarity", 0.0),
                "verdict": det.get("verdict", "SAFE"),
                "risk": _compute_risk(det.get("similarity", 0.0)),
                "action": _compute_action(det.get("similarity", 0.0), det.get("verdict", "SAFE")),
                "confidence": det.get("confidence", 0.0),
                "watermark_id": watermark_id,
                "ownership_verified": ownership_verified,
                "blockchain_tx_hash": blockchain_tx_hash,
                "fingerprint_hash": fingerprint_hash,
                "feature_vector_dimensions": len(feature_vector),
                "leak_source": det.get("leak_source", "unknown"),
                "detected_at": det.get("detected_at", datetime.utcnow().isoformat()),
            })

    # If no detections, produce a single "clean" result
    if not detections:
        detections.append({
            "content_id": content_id,
            "url": "N/A",
            "platform": "N/A",
            "similarity": 0.0,
            "verdict": "SAFE",
            "risk": "LOW",
            "action": "NONE",
            "confidence": 1.0,
            "watermark_id": watermark_id,
            "ownership_verified": ownership_verified,
            "blockchain_tx_hash": blockchain_tx_hash,
            "fingerprint_hash": fingerprint_hash,
            "feature_vector_dimensions": len(feature_vector),
            "leak_source": "none",
            "detected_at": datetime.utcnow().isoformat(),
        })

    return detections


def _compute_risk(similarity: float) -> str:
    if similarity > 0.9:
        return "HIGH"
    elif similarity > 0.7:
        return "MEDIUM"
    return "LOW"


def _compute_action(similarity: float, verdict: str) -> str:
    if similarity > 0.9 and verdict == "PIRACY":
        return "TAKEDOWN"
    elif similarity > 0.7:
        return "MONITOR"
    return "IGNORE"


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python integrated_pipeline.py <media_file_path> [content_id] [owner_id]")
        print("")
        print("Example:")
        print("  python integrated_pipeline.py Layer1-2/test_sample.mp4")
        print("  python integrated_pipeline.py video.mp4 my_content_123 owner_sakshi")
        sys.exit(1)

    file_path = sys.argv[1]
    content_id = sys.argv[2] if len(sys.argv) > 2 else ""
    owner_id = sys.argv[3] if len(sys.argv) > 3 else "owner_default"

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print("  🛡️  AI Digital Content Piracy Detection System")
    print("  End-to-End Integrated Pipeline")
    print(f"  Started at: {datetime.now().isoformat()}")
    print("=" * 60)

    # Pre-flight checks
    print("\n🔍 Pre-flight checks...")
    l12_ok = _check_service("Layer 1-2", LAYER12_URL)
    l37_ok = _check_service("Layer 3-7", MAIN_APP_URL)
    print(f"   Layer 1-2 (port 8001): {'✅ Online' if l12_ok else '❌ Offline'}")
    print(f"   Layer 3-7 (port 8000): {'✅ Online' if l37_ok else '❌ Offline'}")

    if not l12_ok:
        print("\n❌ Layer 1-2 is not running.")
        print("   Start all services with: python run_all.py")
        print("   Or for offline testing: python pipeline_demo.py")
        sys.exit(1)

    try:
        # ── Step 1: Layer 1-2 ────────────────────────────────────────
        layer12_result = step_layer12(file_path, content_id, owner_id)
        content_id = layer12_result["content_id"]

        # ── Step 2: Layer 3-4 ────────────────────────────────────────
        layer34_result = None
        if l37_ok:
            layer34_result = step_layer34(content_id)
        else:
            print("\n⚠️ Layer 3-7 offline — skipping ownership verification")

        # ── Step 3: Layer 5-6-7 ──────────────────────────────────────
        layer56_result = None
        if l37_ok:
            layer56_result = step_layer56(content_id)
        else:
            print("\n⚠️ Layer 3-7 offline — skipping detection scan")

        # ── Build final output ───────────────────────────────────────
        _print_header("FINAL OUTPUT — Structured Detection Results")

        final_output = build_final_output(layer12_result, layer34_result, layer56_result)

        for i, result in enumerate(final_output, 1):
            print(f"\n📋 Detection #{i}:")
            _print_json(result)

        # ── Summary ──────────────────────────────────────────────────
        _print_header("PIPELINE SUMMARY")

        piracy_count = sum(1 for r in final_output if r["verdict"] == "PIRACY")
        suspicious_count = sum(1 for r in final_output if r["verdict"] == "SUSPICIOUS")
        safe_count = sum(1 for r in final_output if r["verdict"] == "SAFE")

        print(f"  Content ID:         {content_id}")
        print(f"  Total Detections:   {len(final_output)}")
        print(f"  🔴 PIRACY:          {piracy_count}")
        print(f"  🟡 SUSPICIOUS:      {suspicious_count}")
        print(f"  🟢 SAFE:            {safe_count}")
        print(f"  Ownership:          {'✅ Verified' if layer34_result and layer34_result.get('ownership_verified') else '❓ Unknown'}")
        print(f"  Completed at:       {datetime.now().isoformat()}")

        # ── Dashboard summary ────────────────────────────────────────
        if l37_ok:
            dashboard = step_dashboard()
            if dashboard:
                print(f"\n📊 Dashboard Summary:")
                print(f"   Total detections (all time): {dashboard.get('total_detections', 0)}")
                print(f"   Piracy (all time):           {dashboard.get('piracy_count', 0)}")
                print(f"   Takedowns executed:          {dashboard.get('takedowns_executed', 0)}")

        # ── Save results ─────────────────────────────────────────────
        output_path = Path(f"pipeline_output_{content_id}.json")
        output_data = {
            "pipeline_run": {
                "content_id": content_id,
                "file_path": str(file_path),
                "owner_id": owner_id,
                "timestamp": datetime.now().isoformat(),
            },
            "layer12": layer12_result,
            "layer34": layer34_result,
            "detections": final_output,
        }
        output_path.write_text(json.dumps(output_data, indent=2, default=str))
        print(f"\n💾 Full results saved to: {output_path}")

        print("\n" + "=" * 60)
        print("  ✅ Pipeline execution complete!")
        print("=" * 60)

    except httpx.ConnectError:
        print("\n❌ Failed to connect to services.")
        print("   Start all services with: python run_all.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()