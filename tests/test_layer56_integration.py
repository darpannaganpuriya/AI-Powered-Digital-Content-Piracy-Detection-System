"""
Run: python tests/test_layer56_integration.py
Tests Layer 5+6 integration WITHOUT starting the server.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crawler_import():
    from app.services.crawler_service import crawl_for_content
    # Simulate metadata
    metadata = {"title": "IPL Highlights", "keywords": ["IPL", "cricket"]}
    print("[crawler] import OK")
    print("[crawler] crawl_for_content function exists:", callable(crawl_for_content))

def test_matcher_import():
    from app.services.matcher_service import match_against_reference
    # Test with fake hashes
    ref = "864cb271f387639a"
    hashes = ["864cb271f387639a", "a3f1b2c4d5e6f7a8"]
    score = match_against_reference(ref, hashes)
    assert 0.0 <= score <= 1.0, f"Score out of range: {score}"
    assert score == 1.0, f"Same hash should score 1.0, got {score}"
    print("[matcher] import OK, similarity:", score)

def test_ai_engine_import():
    from app.services.ai_engine_service import detect_piracy
    verdict, conf = detect_piracy("ipl full highlights free", 0.95, True)
    assert verdict == "PIRACY"
    assert conf == 0.95
    print("[ai_engine] import OK, verdict:", verdict, "confidence:", conf)
    
    verdict2, conf2 = detect_piracy("match highlights", 0.80, True)
    assert verdict2 == "SUSPICIOUS"
    print("[ai_engine] suspicious case OK:", verdict2)

def test_fingerprint_import():
    from app.services.fingerprint_service import extract_hashes, download_and_extract
    print("[fingerprint] import OK")
    print("[fingerprint] extract_hashes exists:", callable(extract_hashes))
    print("[fingerprint] download_and_extract exists:", callable(download_and_extract))

def test_schemas():
    from app.models.schemas import (
        Layer12Input, Layer34Output,
        Layer56Input, Layer56DetectionResult, Layer56Response
    )
    print("[schemas] all Layer56 schemas import OK")
    
    # Test Layer56Input matches Layer34Output fields
    test_input = Layer56Input(
        content_id="test_123",
        fingerprint_hash="864cb271f387639a",
        watermark_id="user_broadcaster_9",
        owner_id="bcci_official",
        blockchain_tx_hash="0xabc123def456",
        ownership_verified=True,
        metadata={"title": "IPL Highlights", "keywords": ["IPL", "cricket"]}
    )
    print("[schemas] Layer56Input created OK:", test_input.content_id)

def test_layer56_service_import():
    from app.services.layer56_service import decode_leak_source, run_detection
    
    # Test decode_leak_source
    assert decode_leak_source("user_broadcaster_9") == "broadcaster"
    assert decode_leak_source("user_456") == "user"
    assert decode_leak_source("platform_hotstar") == "platform"
    assert decode_leak_source("unknown_xyz") == "unknown"
    print("[layer56_service] decode_leak_source all cases OK")
    print("[layer56_service] run_detection exists:", callable(run_detection))

if __name__ == "__main__":
    print("=" * 50)
    print("  LAYER 5+6 INTEGRATION VERIFICATION")
    print("=" * 50)
    
    tests = [
        test_schemas,
        test_matcher_import,
        test_ai_engine_import,
        test_fingerprint_import,
        test_crawler_import,
        test_layer56_service_import,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print("  PASSED\n")
        except Exception as e:
            failed += 1
            print(f"  FAILED: {e}\n")
    
    print("=" * 50)
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  ALL GOOD — Ready to run server")
    else:
        print("  Fix errors above before running server")
    print("=" * 50)
