"""Validate repository JSON files and reject duplicate object keys."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    "bin", "obj", "build", "dist",
}


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def tracked_json_files():
    """Read git's NUL-delimited path list safely, including spaces in names."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "*.json"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        names = [
            item.decode("utf-8")
            for item in result.stdout.split(b"\0")
            if item
        ]
        if names:
            return sorted(ROOT / name for name in names)
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        pass

    return sorted(
        path for path in ROOT.rglob("*.json")
        if not any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts)
    )


def main():
    files = tracked_json_files()
    failures = []
    for path in files:
        try:
            with path.open("r", encoding="utf-8") as stream:
                json.load(stream, object_pairs_hook=reject_duplicate_keys)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            failures.append((path.relative_to(ROOT), str(exc)))

    for path, error in failures:
        print(f"FAIL {path}: {error}")
    if failures:
        print(f"FAIL: {len(failures)} invalid JSON file(s) out of {len(files)}")
        return 1

    print(f"PASS: {len(files)} JSON file(s) valid; duplicate keys checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
