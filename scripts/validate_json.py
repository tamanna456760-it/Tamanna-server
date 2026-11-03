import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}

def main():
    files = sorted(
        p for p in ROOT.rglob("*.json")
        if not any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts)
    )
    failures = []
    for path in files:
        try:
            with path.open(encoding="utf-8") as stream:
                json.load(stream)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            failures.append((path.relative_to(ROOT), str(exc)))
    for path, error in failures:
        print(f"FAIL {path}: {error}")
    if failures:
        print(f"{len(failures)} invalid JSON file(s) out of {len(files)}")
        return 1
    print(f"PASS: {len(files)} JSON file(s) are valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())
