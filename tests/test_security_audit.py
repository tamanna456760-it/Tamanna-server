from pathlib import Path

from scripts.security_audit import audit_repository, inspect_nginx


ROOT = Path(__file__).resolve().parents[1]


def test_current_repository_has_no_failed_security_posture_checks():
    report = audit_repository(ROOT)
    assert report["summary"]["failed"] == 0, report["checks"]


def test_nginx_audit_detects_missing_hsts():
    checks = inspect_nginx('server { add_header X-Frame-Options "DENY" always; }')
    hsts = next(item for item in checks if item["id"] == "nginx.hsts")
    assert hsts["status"] == "fail"
    assert hsts["severity"] == "high"


def test_nginx_audit_warns_about_inline_csp():
    checks = inspect_nginx("add_header Content-Security-Policy \"script-src 'unsafe-inline'\" always;")
    inline = next(item for item in checks if item["id"] == "nginx.csp_inline")
    assert inline["status"] == "warn"
    assert inline["severity"] == "medium"
