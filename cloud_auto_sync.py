"""Legacy daily cloud-sync scheduler; workers must exist before the job can run."""
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKERS = ("tamanna_book_sync.py", "tamanna_drive_sync.py")


def job():
    all_ok = True
    for name in WORKERS:
        worker = ROOT / name
        if not worker.is_file():
            print(f"SKIP: required worker is missing: {name}", flush=True)
            all_ok = False
            continue
        try:
            result = subprocess.run(
                [sys.executable, str(worker)],
                cwd=ROOT,
                check=False,
                timeout=3600,
            )
            print(f"{name} exit code: {result.returncode}", flush=True)
            all_ok = all_ok and result.returncode == 0
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"{name} failed: {type(exc).__name__}", flush=True)
            all_ok = False
    return all_ok


def main():
    print("Tamanna cloud sync scheduler started; schedule: 02:00 local time", flush=True)
    last_run = None
    while True:
        now = datetime.now()
        if now.hour == 2 and now.minute == 0 and last_run != date.today():
            job()
            last_run = date.today()
        time.sleep(20)


if __name__ == "__main__":
    main()
