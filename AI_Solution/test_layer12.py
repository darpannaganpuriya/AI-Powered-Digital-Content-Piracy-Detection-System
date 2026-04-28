import httpx


def test_health():
    try:
        r = httpx.get("http://127.0.0.1:8001/health", timeout=5)
        assert r.status_code == 200
        print("[Layer 1+2] Health check PASSED:", r.json())
    except Exception as e:
        print("[Layer 1+2] Health check FAILED:", e)


if __name__ == "__main__":
    test_health()
