from pathlib import Path
import re

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


def test_production_nginx_csp_does_not_allow_inline_code():
    nginx = (ROOT / "deploy/nginx/tamanna-domains.conf").read_text(encoding="utf-8")
    checks = inspect_nginx(nginx)
    assert not any(item["id"] == "nginx.csp_inline" for item in checks), checks


def test_public_homepage_uses_external_styles_and_script():
    html = (ROOT / "Wabsite/Index.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="assets/css/tamanna-site.css" />' in html
    assert '<script src="assets/js/tamanna-site.js" defer></script>' in html
    assert not re.search(r"<style\b", html, re.I)
    assert not re.search(r"\sstyle\s*=", html, re.I)
    assert not re.search(r"<script>(?!\s*src)[\s\S]*?</script>", html, re.I)
