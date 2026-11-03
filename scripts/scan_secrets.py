"""Basic high-confidence secret scan for tracked text files."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_SUFFIXES = {
    ".dll", ".exe", ".pdb", ".jar", ".png", ".jpg", ".jpeg",
    ".webp", ".gif", ".zip", ".db", ".sqlite", ".pyc",
}
PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "hard-coded credential",
        re.compile(
            r"""(?i)\b(?:api[_-]?key|password|secret[_-]?key|access[_-]?token)\s*[:=]\s*["']([^"']{12,})["']"""
        ),
    ),
]


def tracked_files():
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        return [
            ROOT / item.decode("utf-8")
            for item in result.stdout.split(b"\0")
            if item
        ]
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return sorted(ROOT.rglob("*"))


def main():
    findings = []
    for path in tracked_files():
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if any(part in {".git", ".venv", "venv", "node_modules", "__pycache__", "bin", "obj"} for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for label, pattern in PATTERNS:
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append((path.relative_to(ROOT), line, label))

    if findings:
        for path, line, label in findings:
            print(f"FAIL {path}:{line}: possible {label}")
        print(f"FAIL: {len(findings)} possible secret(s) detected")
        return 1

    print("PASS: no high-confidence hard-coded secret patterns found in tracked text files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
