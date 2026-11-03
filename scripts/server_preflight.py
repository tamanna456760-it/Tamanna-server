#!/usr/bin/env python3
"""Read-only preflight checks before starting the Tamanna container."""
import os
import secrets
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
REQUIRED_TOKEN_BYTES = 32


def main() -> int:
    errors = []
    warnings = []
    if not shutil.which("docker"):
        errors.append("Docker CLI is not installed or not on PATH.")
    else:
        import subprocess
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
        if result.returncode:
            errors.append("Docker Compose plugin is unavailable.")
    if not ENV_FILE.is_file():
        errors.append("Missing .env. Copy .env.example to .env and set ORCHESTRATOR_TOKEN.")
    else:
        token = ""
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ORCHESTRATOR_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
        if len(token.encode("utf-8")) < REQUIRED_TOKEN_BYTES:
            errors.append("ORCHESTRATOR_TOKEN must contain at least 32 bytes.")
        if token.lower() in {"change-this-token", "password", "secret", "changeme"}:
            errors.append("ORCHESTRATOR_TOKEN is a placeholder; generate a unique secret.")
    if not (ROOT / "docker-compose.yml").is_file():
        errors.append("docker-compose.yml is missing.")
    data_dir = ROOT / "data"
    if data_dir.exists() and not data_dir.is_dir():
        errors.append("data exists but is not a directory.")
    if not data_dir.exists():
        warnings.append("data/ will be created by the start script.")
    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print("PASS: local prerequisites and secret configuration look ready.")
    print("Note: this does not verify DNS, TLS, hosting reachability, or production security.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
