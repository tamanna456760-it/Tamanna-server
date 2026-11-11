#!/usr/bin/env python3
"""Read-only security posture audit for the Tamanna server repository.

This checks repository configuration and defensive controls only. It does not
probe hosts, scan ports, exploit vulnerabilities, change files, or contact the
network. A clean report is not a penetration-test certification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def finding(check_id: str, status: str, severity: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "status": status, "severity": severity, "detail": detail}


def inspect_nginx(content: str) -> list[dict[str, str]]:
    checks = []
    required = {
        "nginx.hsts": 'Strict-Transport-Security "max-age=31536000"',
        "nginx.nosniff": 'X-Content-Type-Options "nosniff"',
        "nginx.frame_protection": 'X-Frame-Options "DENY"',
        "nginx.referrer_policy": "Referrer-Policy",
        "nginx.csp": "Content-Security-Policy",
        "nginx.server_tokens": "server_tokens off;",
        "nginx.tls_redirect": "return 301 https://www.bd-king-r7.com$request_uri;",
        "nginx.private_upstream": "proxy_pass http://127.0.0.1:8000;",
    }
    for check_id, marker in required.items():
        checks.append(finding(
            check_id,
            "pass" if marker in content else "fail",
            "high" if check_id in {"nginx.hsts", "nginx.frame_protection", "nginx.private_upstream"} else "medium",
            "Required Nginx control is present." if marker in content else f"Missing required Nginx control: {marker}",
        ))
    if "'unsafe-inline'" in content:
        checks.append(finding(
            "nginx.csp_inline",
            "warn",
            "medium",
            "CSP permits inline scripts or styles; migrate inline code to nonce/hash-based CSP before removing this allowance.",
        ))
    return checks


def audit_repository(root: Path) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def read(relative: str) -> str:
        path = root / relative
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            checks.append(finding(
                f"file.{relative.replace('/', '.')}",
                "fail",
                "high",
                f"Required audit input is missing or unreadable: {relative}",
            ))
            return ""

    ignore = read(".gitignore")
    if any(line.strip() in {".env", ".env.*"} for line in ignore.splitlines()):
        checks.append(finding("secrets.env_ignored", "pass", "high", "Private .env files are ignored by Git."))
    else:
        checks.append(finding("secrets.env_ignored", "fail", "high", "Add .env and .env.* to .gitignore."))

    app = read("app.py")
    app_controls = {
        "app.token_minimum": 'len(token) < 32',
        "app.constant_time_token_compare": "hmac.compare_digest",
        "app.request_size_limit": 'MAX_CONTENT_LENGTH',
        "app.rate_limit": "enforce_rate_limit",
        "app.security_headers": "X-Content-Type-Options",
        "app.exact_origin_allowlist": "origin in CORS_ORIGINS",
    }
    for check_id, marker in app_controls.items():
        checks.append(finding(
            check_id,
            "pass" if marker in app else "fail",
            "high" if check_id in {"app.token_minimum", "app.constant_time_token_compare"} else "medium",
            "Defensive control found in Flask application." if marker in app else f"Expected defensive control not found: {marker}",
        ))

    bridge = read("bridge.py")
    for check_id, marker in {
        "bridge.minimum_token_length": "len(expected) >= 32",
        "bridge.constant_time_compare": "secrets.compare_digest",
    }.items():
        checks.append(finding(
            check_id, "pass" if marker in bridge else "fail", "high",
            "Bridge bearer-token validation is present." if marker in bridge else f"Missing bridge control: {marker}",
        ))

    protocol = read("security/service_protocol.py")
    protocol_controls = {
        "protocol.hmac_signature": "hmac.new",
        "protocol.constant_time_compare": "hmac.compare_digest",
        "protocol.timestamp_window": "CLOCK_SKEW_SECONDS",
        "protocol.replay_protection": "_claim_nonce",
        "protocol.redis_fail_closed": "Fail closed",
    }
    for check_id, marker in protocol_controls.items():
        checks.append(finding(
            check_id, "pass" if marker in protocol else "fail", "high",
            "Service protocol control is present." if marker in protocol else f"Missing service protocol control: {marker}",
        ))

    compose = read("docker-compose.yml")
    for check_id, marker in {
        "docker.orchestrator_loopback": '"127.0.0.1:8000:8000"',
        "docker.ai_loopback": '"127.0.0.1:8001:8000"',
        "docker.no_new_privileges": "no-new-privileges:true",
    }.items():
        checks.append(finding(
            check_id, "pass" if marker in compose else "fail", "high",
            "Container hardening setting is present." if marker in compose else f"Missing container hardening setting: {marker}",
        ))

    dockerfile = read("dockerfile")
    checks.append(finding(
        "docker.non_root_user",
        "pass" if "USER tamanna" in dockerfile else "fail",
        "high",
        "Application container runs as the dedicated non-root user." if "USER tamanna" in dockerfile else "Docker image must run as a non-root user.",
    ))

    nginx = read("deploy/nginx/tamanna-domains.conf")
    checks.extend(inspect_nginx(nginx))

    env_example = read(".env.example")
    secret_names = (
        "ORCHESTRATOR_TOKEN",
        "TAMANNA_SERVICE_SHARED_SECRET",
        "MCP_BEARER_TOKEN",
        "TAMANNA_BRIDGE_SERVICE_TOKEN",
        "TAMANNA_SESSION_SECRET",
    )
    for name in secret_names:
        values = [
            line.split("=", 1)[1].strip()
            for line in env_example.splitlines()
            if line.strip().startswith(name + "=")
        ]
        safe = bool(values) and all(not value or value.startswith("${") for value in values)
        checks.append(finding(
            f"secrets.template_{name.lower()}",
            "pass" if safe else "fail",
            "high",
            "Secret template is blank or environment-substituted." if safe else f"Do not store a real {name} value in .env.example.",
        ))

    statuses = [item["status"] for item in checks]
    summary = {
        "status": "fail" if "fail" in statuses else ("pass_with_warnings" if "warn" in statuses else "pass"),
        "total": len(checks),
        "passed": statuses.count("pass"),
        "warnings": statuses.count("warn"),
        "failed": statuses.count("fail"),
    }
    return {"summary": summary, "checks": checks, "scope": "read_only_repository_configuration_audit"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return non-zero for warnings too.")
    args = parser.parse_args()
    report = audit_repository(args.root.resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Tamanna Server Security Posture Audit")
        print(json.dumps(report["summary"], indent=2))
        for item in report["checks"]:
            print(f'{item["status"].upper():5} [{item["severity"]}] {item["id"]}: {item["detail"]}')
        print("Scope: read-only repository configuration; no network probing or exploitation.")
    failed = report["summary"]["failed"] > 0
    warned = report["summary"]["warnings"] > 0
    return 1 if failed or (args.fail_on_warning and warned) else 0


if __name__ == "__main__":
    raise SystemExit(main())
