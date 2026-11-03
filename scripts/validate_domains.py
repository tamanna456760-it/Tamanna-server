"""Validate the planned domain configuration; this does not query live DNS."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "domains" / "domain_config.json"
DNS_RECORDS = ROOT / "domains" / "cloudflare-dns-records.json"
NEW_DOMAIN = "bd-king-r7.com"
LEGACY_ALIAS = "www.tamanna.com"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    domains = data.get("domains", {})
    primary = domains.get("primary", {})
    onion = domains.get("onion", {})
    require(primary.get("domain") == NEW_DOMAIN, "Primary domain must be bd-king-r7.com")
    require(primary.get("www") == f"www.{NEW_DOMAIN}", "WWW host is incorrect")
    require(primary.get("registration_status") == "unverified", "Do not claim registration without verification")
    require(primary.get("cloudflare_zone_status") == "pending", "Cloudflare pending state must be explicit")
    require(onion.get("enabled") is False, "Tor must remain disabled until a real v3 address is configured")

    aliases = domains.get("legacy_aliases", [])
    alias = next((item for item in aliases if item.get("host") == LEGACY_ALIAS), None)
    require(alias is not None, "www.tamanna.com must remain configured as a legacy alias")
    require(alias.get("redirect_target") == f"https://www.{NEW_DOMAIN}", "Legacy alias must redirect to the canonical HTTPS host")
    require(alias.get("tls_certificate_required") is True, "Legacy HTTPS alias requires its own valid certificate")

    subdomains = data.get("subdomains", {})
    for name in ("api", "admin", "app"):
        require(subdomains.get(name) == f"{name}.{NEW_DOMAIN}", f"{name} hostname is incorrect")

    dns = data.get("dns", {})
    require(dns.get("provider") == "cloudflare", "DNS provider must be Cloudflare")
    require(dns.get("nameservers") == ["pablo.ns.cloudflare.com", "uma.ns.cloudflare.com"],
            "Cloudflare nameservers do not match the supplied dashboard values")

    records = json.loads(DNS_RECORDS.read_text(encoding="utf-8"))
    require(records.get("zone") == NEW_DOMAIN, "DNS records zone mismatch")
    root_record = next((item for item in records.get("records", []) if item.get("name") == "@"), {})
    www_record = next((item for item in records.get("records", []) if item.get("name") == "www"), {})
    require(root_record.get("type") == "A", "Root DNS record must be an A record")
    require(root_record.get("content") == "REPLACE_WITH_REAL_ORIGIN_IPV4",
            "Do not publish a fabricated origin IP")
    require(www_record.get("type") == "CNAME" and www_record.get("content") == NEW_DOMAIN,
            "Canonical www DNS record is incorrect")

    nginx = (ROOT / "deploy" / "nginx" / "tamanna-domains.conf").read_text(encoding="utf-8")
    require(f"server_name {LEGACY_ALIAS};" in nginx, "Nginx must retain the legacy HTTPS alias vhost")
    require(f"return 301 https://www.{NEW_DOMAIN}$request_uri;" in nginx,
            "Nginx must redirect legacy and non-canonical hosts to the canonical host")
    require("/etc/letsencrypt/live/www.tamanna.com/fullchain.pem" in nginx,
            "Legacy alias must reference its TLS certificate")

    security = data.get("security", {})
    require(security.get("https_required") is True, "HTTPS must be required")
    require(security.get("tls_minimum") in {"1.2", "1.3"}, "TLS minimum must be 1.2 or 1.3")
    require(security.get("expose_private_keys") is False, "Private keys must never be exposed")

    print("PASS: bd-king-r7.com is configured as the primary domain")
    print("PASS: www.tamanna.com is retained as a HTTPS redirect alias")
    print("PASS: Cloudflare nameservers match the supplied dashboard")
    print("PASS: DNS origin IP is an explicit placeholder, not a fabricated address")
    print("NOTE: Domain registration, nameserver propagation, live DNS, TLS, and hosting are NOT verified")


if __name__ == "__main__":
    main()
