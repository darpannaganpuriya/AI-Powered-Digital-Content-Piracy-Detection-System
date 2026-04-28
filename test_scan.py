"""Full system verification — checks every layer and endpoint."""
import httpx
import json

print("=" * 60)
print("  FULL SYSTEM VERIFICATION")
print("=" * 60)

checks = []

# 1. Layer 1-2 Health
try:
    r = httpx.get("http://127.0.0.1:8001/health", timeout=5)
    ok = r.status_code == 200
    checks.append(("Layer 1-2 Health", ok))
    print(f"\n1. Layer 1-2 Health:        {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Layer 1-2 Health", False))
    print(f"\n1. Layer 1-2 Health:        FAIL ({e})")

# 2. Layer 1-2 Frontend
try:
    r = httpx.get("http://127.0.0.1:8001/ui", timeout=5)
    ok = r.status_code == 200 and "ContentShield" in r.text
    checks.append(("Layer 1-2 Frontend", ok))
    print(f"2. Layer 1-2 Frontend (UI): {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Layer 1-2 Frontend", False))
    print(f"2. Layer 1-2 Frontend:      FAIL ({e})")

# 3. Frontend CSS
try:
    r = httpx.get("http://127.0.0.1:8001/style.css", timeout=5)
    ok = r.status_code == 200 and len(r.text) > 100
    checks.append(("Frontend CSS", ok))
    print(f"3. Frontend CSS:            {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Frontend CSS", False))
    print(f"3. Frontend CSS:            FAIL ({e})")

# 4. Frontend JS
try:
    r = httpx.get("http://127.0.0.1:8001/script.js", timeout=5)
    ok = r.status_code == 200 and len(r.text) > 100
    checks.append(("Frontend JS", ok))
    print(f"4. Frontend JS:             {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Frontend JS", False))
    print(f"4. Frontend JS:             FAIL ({e})")

# 5. Layer 3-7 Health
try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/health", timeout=5)
    ok = r.status_code == 200
    checks.append(("Layer 3-7 Health", ok))
    print(f"5. Layer 3-7 Health:        {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Layer 3-7 Health", False))
    print(f"5. Layer 3-7 Health:        FAIL ({e})")

# 6. Layer 3-4 Content Registration (content 001)
try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/layers/3-4/content/001", timeout=5)
    ok = r.status_code == 200 and r.json().get("ownership_verified") == True
    checks.append(("Layer 3-4 Content 001", ok))
    print(f"6. Layer 3-4 Content (001): {'PASS' if ok else 'FAIL'}")
    if ok:
        d = r.json()
        print(f"   Blockchain TX:           {d['blockchain_tx_hash'][:20]}...")
        print(f"   Ownership Verified:      {d['ownership_verified']}")
        print(f"   Feature Vector:          {len(d['feature_vector'])} dimensions")
except Exception as e:
    checks.append(("Layer 3-4 Content 001", False))
    print(f"6. Layer 3-4 Content (001): FAIL ({e})")

# 7. Layer 5-6 Scan Endpoint
try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/layer56/scan/001", timeout=5)
    ok = r.status_code == 200
    checks.append(("Layer 5-6 Scan Endpoint", ok))
    print(f"7. Layer 5-6 Scan:          {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Layer 5-6 Scan Endpoint", False))
    print(f"7. Layer 5-6 Scan:          FAIL ({e})")

# 8. Dashboard Summary
try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/dashboard/summary", timeout=5)
    ok = r.status_code == 200 and "total_detections" in json.dumps(r.json())
    checks.append(("Dashboard Summary", ok))
    print(f"8. Dashboard Summary:       {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Dashboard Summary", False))
    print(f"8. Dashboard Summary:       FAIL ({e})")

# 9. Decision Endpoint
try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/dashboard/decisions", timeout=5)
    ok = r.status_code == 200
    checks.append(("Decision Endpoint", ok))
    print(f"9. Decision Endpoint:       {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Decision Endpoint", False))
    print(f"9. Decision Endpoint:       FAIL ({e})")

# 10. Predictions Endpoint
try:
    r = httpx.get("http://127.0.0.1:8000/api/v1/dashboard/predictions", timeout=5)
    ok = r.status_code == 200
    checks.append(("Predictions Endpoint", ok))
    print(f"10. Predictions Endpoint:   {'PASS' if ok else 'FAIL'}")
except Exception as e:
    checks.append(("Predictions Endpoint", False))
    print(f"10. Predictions Endpoint:   FAIL ({e})")

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print(f"  RESULT: {passed}/{total} checks passed")
if passed == total:
    print("  ALL SYSTEMS OPERATIONAL!")
else:
    for name, ok in checks:
        if not ok:
            print(f"  FAILED: {name}")
print("=" * 60)
