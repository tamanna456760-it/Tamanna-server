"""Regression checks for the static website's strict Content Security Policy."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "Wabsite"


def test_website_uses_external_assets_without_inline_execution():
    html = (WEB / "Index.html").read_text(encoding="utf-8")
    assert not re.search(r"<style\\b|\\sstyle\\s*=", html, re.IGNORECASE)
    script_tags = re.findall(r"<script([^>]*)>", html, re.IGNORECASE)
    executable_inline = [
        attrs for attrs in script_tags
        if "application/ld+json" not in attrs.lower() and "src=" not in attrs.lower()
    ]
    assert executable_inline == []
    assert (WEB / "assets" / "site.css").is_file()
    assert (WEB / "assets" / "site.js").is_file()


def test_all_static_server_csp_policies_reject_inline_scripts_and_styles():
    nginx = (ROOT / "deploy" / "nginx" / "tamanna-domains.conf").read_text(encoding="utf-8")
    node = (ROOT / "server.js").read_text(encoding="utf-8")
    for policy in (nginx, node):
        assert "script-src 'self'" in policy
        assert "style-src 'self' https://fonts.googleapis.com" in policy
        assert "'unsafe-inline'" not in policy
