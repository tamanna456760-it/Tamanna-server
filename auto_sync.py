"""Legacy daily book-sync scheduler; missing workers are reported, never shell-executed."""
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKER = ROOT / "tamanna_book_sync.py"


def job():
    if not WORKER.is_file():
        print(f"SKIP: required worker is missing: {WORKER.name}", flush=True)
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(WORKER)],
            cwd=ROOT,
            check=False,
            timeout=3600,
        )
        print(f"Book sync exit code: {result.returncode}", flush=True)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Book sync failed: {type(exc).__name__}", flush=True)
        return False


def main():
    print("Tamanna daily sync scheduler started; schedule: 03:00 local time", flush=True)
    last_run = None
    while True:
        now = datetime.now()
        if now.hour == 3 and now.minute == 0 and last_run != date.today():
            job()
            last_run = date.today()
        time.sleep(20)


if __name__ == "__main__":
    main()
