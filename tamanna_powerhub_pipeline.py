#!/usr/bin/env python3
"""Run real repository checks; never fabricate test, scan, or signing results."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

CHECKS = [
    ("Python syntax", [PYTHON, "-m", "compileall", "-q",
                       "app.py", "server.py", "agent.py", "apps.py",
                       "synce.py", "tests", "scripts"]),
    ("JSON validation", [PYTHON, "scripts/validate_json.py"]),
    ("Domain configuration", [PYTHON, "scripts/validate_domains.py"]),
    ("Python tests", [PYTHON, "-m", "pytest", "-q"]),
]


def main():
    failures = 0
    for label, command in CHECKS:
        print(f"\n== {label} ==")
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=False,
        )
        print(result.stdout or "(no output)")
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'}: {label}")
        failures += result.returncode != 0

    if shutil.which("pip-audit"):
        print("\n== Dependency audit ==")
        result = subprocess.run(
            ["pip-audit", "-r", "requirements.txt"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=False,
        )
        print(result.stdout or "(no output)")
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'}: Dependency audit")
        failures += result.returncode != 0
    else:
        print("\nSKIP: pip-audit is not installed; no vulnerability result is claimed.")

    print(f"\nRESULT: {failures} check(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
