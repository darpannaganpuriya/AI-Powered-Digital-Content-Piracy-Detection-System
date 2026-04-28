import time

def start_scheduler(run_pipeline):
    while True:
        print("\n🚀 Running Scan Cycle...")
        run_pipeline()
        time.sleep(3600)  # 1 hour