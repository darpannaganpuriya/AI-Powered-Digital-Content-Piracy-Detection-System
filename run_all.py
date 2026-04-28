#!/usr/bin/env python3
"""
run_all.py — Start all services for the Piracy Detection System.

Launches:
  - Layer 1+2  (port 8001): DRM + Watermark + Fingerprint
  - Layer 3-7  (port 8000): Ownership + Detection + Decision

Each server runs as a subprocess so both are alive simultaneously.
Press Ctrl+C to shut down everything.
"""

import os
import sys
import signal
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LAYERS = [
    {
        "name": "Layer 1+2 | DRM + Watermark + Fingerprint",
        "cwd": os.path.join(BASE_DIR, "Layer1-2", "backend"),
        "app": "app:app",
        "host": "127.0.0.1",
        "port": 8001,
    },
    {
        "name": "Layer 3+4+5+6+7 | Ownership + Detection + Decision",
        "cwd": BASE_DIR,
        "app": "app.main:app",
        "host": "127.0.0.1",
        "port": 8000,
    },
]


def main():
    processes = []

    print("=" * 70)
    print("  AI Digital Content Piracy Detection System")
    print("  Starting all layers...")
    print("=" * 70)

    for layer in LAYERS:
        cmd = [
            sys.executable, "-m", "uvicorn",
            layer["app"],
            "--host", layer["host"],
            "--port", str(layer["port"]),
        ]

        print(f"\n🚀 Starting: {layer['name']}")
        print(f"   URL: http://{layer['host']}:{layer['port']}")
        print(f"   CWD: {layer['cwd']}")

        proc = subprocess.Popen(
            cmd,
            cwd=layer["cwd"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        processes.append(proc)
        time.sleep(1)  # small delay between launches

    print("\n" + "=" * 70)
    print("  All services started!")
    print("  Layer 1-2:  http://127.0.0.1:8001  (docs: /docs)")
    print("  Layer 3-7:  http://127.0.0.1:8000  (docs: /docs)")
    print("")
    print("  Run the pipeline:")
    print("    python integrated_pipeline.py <media_file>")
    print("    python pipeline_demo.py  (offline, no servers needed)")
    print("")
    print("  Press Ctrl+C to stop all services.")
    print("=" * 70)

    def shutdown(signum=None, frame=None):
        print("\n🛑 Shutting down all services...")
        for proc in processes:
            try:
                proc.terminate()
            except Exception:
                pass
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        print("✅ All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Wait for any process to exit
    try:
        while True:
            for proc in processes:
                retcode = proc.poll()
                if retcode is not None:
                    print(f"\n⚠️ A process exited with code {retcode}")
                    shutdown()
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
